import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { BitwardenClient } from '@bitwarden/sdk';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-06-20' });

export async function POST(req: NextRequest) {
  const { priceId, quantity } = await req.json();

  // Pull secrets from Bitwarden
  const client = new BitwardenClient();
  await client.login({ email: process.env.BITWARDEN_EMAIL!, password: process.env.BITWARDEN_PASSWORD! });
  const secretItem = await client.getItem('cloudcommerce-keys');
  const openrouterKey = secretItem.fields.find(f => f.name === 'OPENROUTER')?.value;
  const stripeKey = secretItem.fields.find(f => f.name === 'STRIPE')?.value;

  if (!stripeKey) throw new Error('Stripe key not found in Bitwarden');

  const stripeClient = new Stripe(stripeKey, { apiVersion: '2024-06-20' });

  const session = await stripeClient.checkout.sessions.create({
    line_items: [{ price: priceId, quantity }],
    mode: 'subscription',
    success_url: `${req.headers.get('origin')}/submit?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${req.headers.get('origin')}/pay`,
  });

  return NextResponse.json({ url: session.url });
}

// Rotation endpoint (called by cron)
export async function POST_rotate(req: NextRequest) {
  const client = new BitwardenClient();
  await client.login({ email: process.env.BITWARDEN_EMAIL!, password: process.env.BITWARDEN_PASSWORD! });

  // Generate new OpenRouter key (example)
  const newKey = crypto.randomBytes(32).toString('hex');
  await client.setItem('cloudcommerce-keys', { fields: [{ name: 'OPENROUTER', value: newKey }] });

  // Update services (e.g., restart Render via API)
  // ...

  return NextResponse.json({ success: true });
}