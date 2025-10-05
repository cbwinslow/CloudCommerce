import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def setup_products_and_prices():
    """Create or update Stripe products and prices"""
    products = [
        {
            "id": "free",
            "name": "Free",
            "description": "Basic listing features",
            "monthly_listings": 5,
            "price_monthly": 0,
            "features": [
                "5 listings per month",
                "Basic AI analysis",
                "Single marketplace export"
            ]
        },
        {
            "id": "pro",
            "name": "Pro",
            "description": "For power sellers",
            "monthly_listings": 100,
            "price_monthly": 1999,  # $19.99 in cents
            "features": [
                "100 listings per month",
                "Advanced AI features",
                "Multiple marketplace exports",
                "Basic analytics"
            ]
        },
        {
            "id": "unlimited",
            "name": "Unlimited",
            "description": "For high-volume sellers",
            "monthly_listings": 0,  # 0 means unlimited
            "price_monthly": 9999,  # $99.99 in cents
            "features": [
                "Unlimited listings",
                "Priority support",
                "Advanced analytics",
                "Dedicated account manager"
            ]
        }
    ]

    created_plans = {}
    
    for plan in products:
        # Create or update product
        product = stripe.Product.create(
            id=f"plan_{plan['id']}",
            name=plan["name"],
            description=plan["description"],
            metadata={
                "monthly_listings": plan["monthly_listings"],
                "features": ", ".join(plan["features"])
            }
        )
        
        # Create price if it doesn't exist
        prices = stripe.Price.list(product=product.id)
        if not prices.data:
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan["price_monthly"],
                currency="usd",
                recurring={"interval": "month"},
                metadata={"plan_id": plan["id"]}
            )
        else:
            price = prices.data[0]
        
        created_plans[plan["id"]] = {
            "product_id": product.id,
            "price_id": price.id,
            "stripe_product": product,
            "stripe_price": price
        }
        
        print(f"✅ Created/Updated {plan['name']} plan:")
        print(f"   Product ID: {product.id}")
        print(f"   Price ID: {price.id}")
        print(f"   Price: ${price.unit_amount/100:.2f}/month")
        print(f"   Monthly listings: {plan['monthly_listings'] or 'Unlimited'}")
        print()
    
    return created_plans

if __name__ == "__main__":
    print("🔄 Setting up Stripe products and prices...\n")
    try:
        plans = setup_products_and_prices()
        print("\n✅ Setup complete! Add these to your .env file:")
        print(f"STRIPE_FREE_PLAN_ID={plans['free']['price_id']}")
        print(f"STRIPE_PRO_PLAN_ID={plans['pro']['price_id']}")
        print(f"STRIPE_UNLIMITED_PLAN_ID={plans['unlimited']['price_id']}")
    except Exception as e:
        print(f"\n❌ Error setting up Stripe: {str(e)}")
