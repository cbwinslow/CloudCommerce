import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

// Get current subscription
export async function GET() {
  try {
    const { userId } = auth();
    
    if (!userId) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    // In a real app, you would fetch this from your database
    // This is a simplified example
    const user = await prisma?.user.findUnique({
      where: { id: userId },
      select: {
        subscriptionPlanId: true,
        subscriptionStatus: true,
        subscriptionEndDate: true,
        stripeCustomerId: true,
        stripeSubscriptionId: true,
      },
    });

    if (!user) {
      return new NextResponse('User not found', { status: 404 });
    }

    // Get current month's usage
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    
    const usage = await prisma?.subscriptionUsage.upsert({
      where: {
        userId_month: {
          userId,
          month: firstDay,
        },
      },
      create: {
        userId,
        month: firstDay,
        listingsUsed: 0,
      },
      update: {},
    });

    // Get plan details
    const plan = await prisma?.subscriptionPlan.findUnique({
      where: { id: user.subscriptionPlanId || 'free' },
    });

    return NextResponse.json({
      plan: {
        id: plan?.id,
        name: plan?.name,
        monthly_listings: plan?.monthlyListings,
        features: plan?.features || [],
      },
      status: user.subscriptionStatus,
      current_period_end: user.subscriptionEndDate,
      usage: {
        current: usage?.listingsUsed || 0,
        limit: plan?.monthlyListings || 0,
        remaining: Math.max(0, (plan?.monthlyListings || 0) - (usage?.listingsUsed || 0)),
      },
    });
  } catch (error) {
    console.error('Error fetching subscription:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

// Create or update subscription
export async function POST(req: Request) {
  try {
    const { userId } = auth();
    const { planId } = await req.json();
    
    if (!userId) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    // Get user and plan details
    const [user, plan] = await Promise.all([
      prisma?.user.findUnique({
        where: { id: userId },
        select: { email: true, stripeCustomerId: true },
      }),
      prisma?.subscriptionPlan.findUnique({
        where: { id: planId },
      }),
    ]);

    if (!plan) {
      return new NextResponse('Plan not found', { status: 404 });
    }

    // Create or get Stripe customer
    let customer;
    if (user?.stripeCustomerId) {
      customer = await stripe.customers.retrieve(user.stripeCustomerId);
    } else if (user?.email) {
      customer = await stripe.customers.create({
        email: user.email,
        metadata: { userId },
      });
      
      // Save customer ID to user
      await prisma?.user.update({
        where: { id: userId },
        data: { stripeCustomerId: customer.id },
      });
    }

    if (!customer || !('id' in customer)) {
      return new NextResponse('Error creating customer', { status: 500 });
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customer.id,
      payment_method_types: ['card'],
      subscription_data: {
        metadata: {
          userId,
          planId: plan.id,
        },
      },
      line_items: [
        {
          price: plan.stripePriceId,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/dashboard?success=true`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/subscription?canceled=true`,
    });

    return NextResponse.json({ id: session.id });
  } catch (error) {
    console.error('Error creating subscription:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

// Cancel subscription
export async function DELETE() {
  try {
    const { userId } = auth();
    
    if (!userId) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const user = await prisma?.user.findUnique({
      where: { id: userId },
      select: { stripeSubscriptionId: true },
    });

    if (!user?.stripeSubscriptionId) {
      return new NextResponse('No active subscription', { status: 400 });
    }

    // Cancel subscription at period end
    await stripe.subscriptions.update(user.stripeSubscriptionId, {
      cancel_at_period_end: true,
    });

    // Update user in database
    await prisma?.user.update({
      where: { id: userId },
      data: {
        subscriptionStatus: 'cancelled',
        subscriptionEndDate: new Date(
          new Date().setMonth(new Date().getMonth() + 1)
        ),
      },
    });

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error canceling subscription:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
