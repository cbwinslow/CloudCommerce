from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import stripe
import os
from supabase import create_client
from pydantic import BaseModel

router = APIRouter(prefix="/api/subscription", tags=["subscription"])

# Initialize Stripe and Supabase
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class SubscribeRequest(BaseModel):
    plan_id: str
    payment_method_id: str

class UpdatePaymentMethodRequest(BaseModel):
    payment_method_id: str

# Helper function to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # In a real implementation, verify the JWT token with your auth service
    try:
        # This is a placeholder - replace with actual token verification
        user_id = token  # Simplified for example
        return {"id": user_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status"""
    try:
        # Get user's subscription details
        user_data = supabase.table("users").select("*").eq("id", current_user["id"]).execute()
        if not user_data.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        user = user_data.data[0]
        plan_id = user.get("subscription_plan_id", "free")
        
        # Get plan details
        plan_data = supabase.table("subscription_plans").select("*").eq("id", plan_id).execute()
        plan = plan_data.data[0] if plan_data.data else None
        
        if not plan:
            raise HTTPException(status_code=500, detail="Subscription plan not found")
            
        # Get current month's usage
        current_month = datetime.utcnow().strftime("%Y-%m-01")
        usage_data = supabase.table("subscription_usage")\
            .select("listings_used")\
            .eq("user_id", current_user["id"])\
            .eq("month", current_month)\
            .execute()
            
        listings_used = usage_data.data[0]["listings_used"] if usage_data.data else 0
        
        return {
            "plan": {
                "id": plan["id"],
                "name": plan["name"],
                "monthly_listings": plan["monthly_listings"],
                "features": plan["features"],
            },
            "status": user.get("subscription_status", "inactive"),
            "current_period_end": user.get("subscription_end_date"),
            "usage": {
                "current": listings_used,
                "limit": plan["monthly_listings"],
                "remaining": max(0, plan["monthly_listings"] - listings_used) if plan["monthly_listings"] > 0 else float('inf')
            },
            "next_billing_date": user.get("next_billing_date")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
async def list_plans():
    """List all available subscription plans"""
    try:
        plans_data = supabase.table("subscription_plans").select("*").execute()
        return [{
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "monthly_listings": p["monthly_listings"],
            "price_monthly": float(p["price_monthly"]) if p["price_monthly"] is not None else None,
            "price_yearly": float(p["price_yearly"]) if p.get("price_yearly") else None,
            "features": p["features"]
        } for p in plans_data.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def subscribe(request: SubscribeRequest, current_user: dict = Depends(get_current_user)):
    """Subscribe to a plan or update existing subscription"""
    try:
        # Get plan details
        plan_data = supabase.table("subscription_plans").select("*").eq("id", request.plan_id).execute()
        if not plan_data.data:
            raise HTTPException(status_code=400, detail="Invalid plan ID")
            
        plan = plan_data.data[0]
        
        # Get or create Stripe customer
        user_data = supabase.table("users").select("stripe_customer_id").eq("id", current_user["id"]).execute()
        stripe_customer_id = user_data.data[0].get("stripe_customer_id") if user_data.data else None
        
        if not stripe_customer_id:
            # Create a new Stripe customer
            customer = stripe.Customer.create(
                payment_method=request.payment_method_id,
                email=current_user.get("email"),
                invoice_settings={
                    'default_payment_method': request.payment_method_id
                }
            )
            stripe_customer_id = customer.id
            
            # Save Stripe customer ID to user
            supabase.table("users").update({"stripe_customer_id": stripe_customer_id})\
                .eq("id", current_user["id"]).execute()
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{
                'price': plan["stripe_price_id"],
            }],
            expand=['latest_invoice.payment_intent'],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
        )
        
        # Update user's subscription in database
        now = datetime.utcnow()
        next_billing = datetime.utcnow() + timedelta(days=30)  # Adjust based on billing cycle
        
        supabase.table("users").update({
            "subscription_plan_id": plan["id"],
            "subscription_status": "active",
            "subscription_start_date": now,
            "subscription_end_date": next_billing,
            "next_billing_date": next_billing,
            "stripe_subscription_id": subscription.id
        }).eq("id", current_user["id"]).execute()
        
        # Log subscription change
        supabase.table("subscription_history").insert({
            "user_id": current_user["id"],
            "plan_id": plan["id"],
            "action": "subscribed",
            "metadata": {
                "stripe_subscription_id": subscription.id,
                "previous_plan": user_data.data[0].get("subscription_plan_id") if user_data.data else None
            }
        }).execute()
        
        return {
            "status": "success",
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret,
            "next_billing_date": next_billing.isoformat()
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """Cancel the current subscription at the end of the billing period"""
    try:
        # Get user's subscription
        user_data = supabase.table("users").select("stripe_subscription_id").eq("id", current_user["id"]).execute()
        subscription_id = user_data.data[0].get("stripe_subscription_id") if user_data.data else None
        
        if not subscription_id:
            raise HTTPException(status_code=400, detail="No active subscription found")
            
        # Cancel subscription at period end
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
        # Update user's subscription status
        supabase.table("users").update({
            "subscription_status": "cancelled",
            "subscription_end_date": datetime.fromtimestamp(subscription.current_period_end)
        }).eq("id", current_user["id"]).execute()
        
        # Log subscription change
        supabase.table("subscription_history").insert({
            "user_id": current_user["id"],
            "action": "cancelled",
            "metadata": {
                "stripe_subscription_id": subscription_id,
                "cancellation_effective_date": datetime.fromtimestamp(subscription.current_period_end).isoformat()
            }
        }).execute()
        
        return {"status": "success", "message": "Subscription will be cancelled at the end of the billing period"}
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
