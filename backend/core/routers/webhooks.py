from fastapi import APIRouter, Request, HTTPException, status
import stripe
import os
from supabase import create_client
from datetime import datetime
import json

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# Initialize Stripe and Supabase
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# Webhook secret for verifying events
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    event_type = event['type']
    event_data = event['data']['object']
    
    try:
        if event_type == 'customer.subscription.created':
            await handle_subscription_created(event_data)
        elif event_type == 'customer.subscription.updated':
            await handle_subscription_updated(event_data)
        elif event_type == 'customer.subscription.deleted':
            await handle_subscription_deleted(event_data)
        elif event_type == 'invoice.payment_succeeded':
            await handle_invoice_payment_succeeded(event_data)
        elif event_type == 'invoice.payment_failed':
            await handle_invoice_payment_failed(event_data)
            
    except Exception as e:
        # Log the error
        print(f"Error handling {event_type}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing webhook: {str(e)}")
    
    return {"status": "success"}

async def handle_subscription_created(subscription):
    """Handle subscription creation"""
    customer_id = subscription.customer
    
    # Get the user associated with this customer
    user_data = supabase.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
    if not user_data.data:
        return
        
    user_id = user_data.data[0]["id"]
    
    # Get plan ID from subscription
    plan_id = None
    if subscription.items.data:
        price_id = subscription.items.data[0].price.id
        plan_data = supabase.table("subscription_plans").select("id").eq("stripe_price_id", price_id).execute()
        if plan_data.data:
            plan_id = plan_data.data[0]["id"]
    
    # Update user's subscription
    update_data = {
        "subscription_status": subscription.status,
        "stripe_subscription_id": subscription.id,
        "subscription_start_date": datetime.fromtimestamp(subscription.current_period_start),
        "subscription_end_date": datetime.fromtimestamp(subscription.current_period_end),
        "next_billing_date": datetime.fromtimestamp(subscription.current_period_end)
    }
    
    if plan_id:
        update_data["subscription_plan_id"] = plan_id
    
    supabase.table("users").update(update_data).eq("id", user_id).execute()
    
    # Log the subscription change
    supabase.table("subscription_history").insert({
        "user_id": user_id,
        "plan_id": plan_id,
        "action": "created",
        "metadata": {
            "stripe_subscription_id": subscription.id,
            "status": subscription.status
        }
    }).execute()

async def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    customer_id = subscription.customer
    
    # Get the user associated with this customer
    user_data = supabase.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
    if not user_data.data:
        return
        
    user_id = user_data.data[0]["id"]
    
    # Get plan ID from subscription
    plan_id = None
    if subscription.items.data:
        price_id = subscription.items.data[0].price.id
        plan_data = supabase.table("subscription_plans").select("id").eq("stripe_price_id", price_id).execute()
        if plan_data.data:
            plan_id = plan_data.data[0]["id"]
    
    # Update user's subscription
    update_data = {
        "subscription_status": subscription.status,
        "subscription_end_date": datetime.fromtimestamp(subscription.current_period_end),
        "next_billing_date": datetime.fromtimestamp(subscription.current_period_end)
    }
    
    if plan_id:
        update_data["subscription_plan_id"] = plan_id
    
    # If subscription is cancelled but still active until period end
    if subscription.cancel_at_period_end:
        update_data["subscription_status"] = "cancelled"
    
    supabase.table("users").update(update_data).eq("id", user_id).execute()
    
    # Log the subscription change
    action = "cancelled" if subscription.cancel_at_period_end else "updated"
    
    supabase.table("subscription_usage").insert({
        "user_id": user_id,
        "action": action,
        "metadata": {
            "stripe_subscription_id": subscription.id,
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end
        },
        "created_at": datetime.utcnow().isoformat()
    }).execute()

async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation/expiration"""
    customer_id = subscription.customer
    
    # Get the user associated with this customer
    user_data = supabase.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
    if not user_data.data:
        return
        
    user_id = user_data.data[0]["id"]
    
    # Downgrade to free plan
    update_data = {
        "subscription_status": "expired",
        "subscription_plan_id": "free",
        "subscription_end_date": datetime.utcnow(),
        "next_billing_date": None,
        "stripe_subscription_id": None
    }
    
    supabase.table("users").update(update_data).eq("id", user_id).execute()
    
    # Log the subscription change
    supabase.table("subscription_history").insert({
        "user_id": user_id,
        "plan_id": "free",
        "action": "expired",
        "metadata": {
            "previous_subscription_id": subscription.id,
            "reason": "subscription_deleted"
        }
    }).execute()

async def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment"""
    customer_id = invoice.customer
    
    # Get the user associated with this customer
    user_data = supabase.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
    if not user_data.data:
        return
        
    user_id = user_data.data[0]["id"]
    
    # Update next billing date
    if hasattr(invoice, 'lines') and hasattr(invoice.lines, 'data'):
        for line in invoice.lines.data:
            if hasattr(line, 'period') and hasattr(line.period, 'end'):
                next_billing = datetime.fromtimestamp(line.period.end)
                supabase.table("users")\
                    .update({"next_billing_date": next_billing})\
                    .eq("id", user_id)\
                    .execute()
                break
    
    # Log the payment
    supabase.table("billing_history").insert({
        "user_id": user_id,
        "stripe_invoice_id": invoice.id,
        "amount": invoice.amount_paid / 100,  # Convert from cents to dollars
        "currency": invoice.currency.upper(),
        "status": "succeeded",
        "billing_period_start": datetime.fromtimestamp(invoice.period_start) if hasattr(invoice, 'period_start') else None,
        "billing_period_end": datetime.fromtimestamp(invoice.period_end) if hasattr(invoice, 'period_end') else None,
        "metadata": {
            "invoice_pdf": invoice.invoice_pdf,
            "hosted_invoice_url": invoice.hosted_invoice_url
        }
    }).execute()

async def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment"""
    customer_id = invoice.customer
    
    # Get the user associated with this customer
    user_data = supabase.table("users").select("id").eq("stripe_customer_id", customer_id).execute()
    if not user_data.data:
        return
        
    user_id = user_data.data[0]["id"]
    
    # Log the failed payment
    supabase.table("billing_history").insert({
        "user_id": user_id,
        "stripe_invoice_id": invoice.id,
        "amount": invoice.amount_due / 100,  # Convert from cents to dollars
        "currency": invoice.currency.upper(),
        "status": "failed",
        "billing_period_start": datetime.fromtimestamp(invoice.period_start) if hasattr(invoice, 'period_start') else None,
        "billing_period_end": datetime.fromtimestamp(invoice.period_end) if hasattr(invoice, 'period_end') else None,
        "failure_reason": invoice.billing_reason if hasattr(invoice, 'billing_reason') else None,
        "metadata": {
            "attempted_payment_method": invoice.payment_intent.payment_method if hasattr(invoice, 'payment_intent') else None,
            "next_payment_attempt": datetime.fromtimestamp(invoice.next_payment_attempt) if hasattr(invoice, 'next_payment_attempt') else None
        }
    }).execute()
    
    # Optionally, send a notification to the user about the failed payment
    # This would integrate with your notification system
    # await send_payment_failed_notification(user_id, invoice)
