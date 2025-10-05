import stripe
from supabase import create_client
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

async def check_credits(user_id: str):
    { data } = supabase.table("users").select("credits, sub_status").eq("id", user_id).execute()
    if data[0]["credits"] < 1 and data[0]["sub_status"] != "unlimited":
        return False
    return True

async def deduct_credit(user_id: str):
    supabase.table("users").update({"credits": supabase.sql("credits - 1")}).eq("id", user_id).execute()

@stripe.webhook.create("checkout.session.completed")
async def handle_payment(event):
    session = event.data.object
    user_id = session.metadata.user_id
    if session.mode == "payment":
        supabase.table("users").update({"credits": supabase.sql("credits + 1")}).eq("id", user_id).execute()
    elif session.mode == "subscription":
        supabase.table("users").update({"sub_status": "active"}).eq("id", user_id).execute()