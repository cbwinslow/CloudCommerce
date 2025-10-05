import { NextRequest, NextResponse } from 'next/server';
import { currentUser } from '@clerk/nextjs/server';
import { createClient } from '@supabase/supabase-js';
import Papa from 'papaparse';
import { analyzeItem, generateListings } from '@/lib/openrouter';
import { scrapeSimilarItems } from '@/lib/scraper';
import { runCrewAI } from '@/lib/crew';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2023-10-16' });
const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!);

export async function POST(req: NextRequest) {
  const user = await currentUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // Check credits (from Supabase)
  const { data: userData } = await supabase.from('users').select('credits, sub_status').eq('id', user.id).single();
  if (userData?.credits < 1 && userData?.sub_status !== 'unlimited') {
    return NextResponse.json({ error: 'Insufficient credits. Please purchase more.' }, { status: 402 });
  }

  try {
    const formData = await req.formData();
    const images = formData.getAll('images') as File[];
    const summary = formData.get('summary') as string;
    const category = formData.get('category') as string;
    const condition = formData.get('condition') as string;

    // Upload images transiently (Vercel Blob or temp URLs)
    const imageUrls = await Promise.all(images.map(async (img) => {
      // Pseudo-code: Upload to Vercel Blob/R2, get URL, schedule delete after 1h
      // For now, assume base64 or temp URL
      return URL.createObjectURL(img); // Temp for dev
    }));

    // Run CrewAI for full workflow
    const crewResult = await runCrewAI(imageUrls, summary, category, condition);

    // Fallback to direct LLM if CrewAI down
    const analysis = crewResult.analysis || await analyzeItem(imageUrls, summary, category, condition);

    // Scrape for pricing
    const scraped = await scrapeSimilarItems(summary);

    // Enhance analysis with scraped data
    const enhancedPrompt = `${analysis}. Scraped data: ${JSON.stringify(scraped)}.`;
    const listings = await generateListings(enhancedPrompt, ['ebay', 'amazon', 'facebook']);

    // Generate CSV
    const csv = `Platform,Title,Description,Price,Condition\n${Object.entries(listings).map(([platform, item]: any) => 
      `${platform},"${item.title}","${item.description}",$${item.price},"${item.condition}"`
    ).join('\n')}`;

    // Deduct credit
    if (userData?.credits > 0) {
      await supabase.from('users').update({ credits: userData.credits - 1 }).eq('id', user.id);
    }

    // Log submission for history/compliance
    await supabase.from('submissions').insert({
      user_id: user.id,
      summary,
      analysis,
      listings,
      // Images deleted after processing
    });

    return NextResponse.json({ listings, csv, recommendedPrice: scraped.recommendedPrice, arbitrage: scraped.arbitrage || [] });

  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Processing failed' }, { status: 500 });
  }
}

// Stripe webhook for payments (per-use/sub)
export async function POST_webhook(req: NextRequest) {
  const sig = req.headers.get('stripe-signature')!;
  const body = await req.text();

  let event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    return NextResponse.json({ error: 'Webhook signature verification failed' }, { status: 400 });
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session;
    const userId = session.metadata?.userId;
    if (session.payment_status === 'paid') {
      // Add credits or set sub
      if (session.mode === 'payment') {
        await supabase.from('users').update({ credits: supabase.row(userId).credits + 1 }).eq('id', userId);
      } else if (session.mode === 'subscription') {
        await supabase.from('users').update({ sub_status: 'active' }).eq('id', userId);
      }
    }
  }

  return NextResponse.json({ received: true });
}
