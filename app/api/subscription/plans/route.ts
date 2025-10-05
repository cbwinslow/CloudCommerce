import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // In a real app, you would fetch this from your database
    const plans = await prisma?.subscriptionPlan.findMany({
      orderBy: { priceMonthly: 'asc' },
    });

    // Format the response
    const formattedPlans = (plans || []).map((plan) => ({
      id: plan.id,
      name: plan.name,
      description: plan.description,
      monthly_listings: plan.monthlyListings,
      price_monthly: Number(plan.priceMonthly),
      price_yearly: plan.priceYearly ? Number(plan.priceYearly) : undefined,
      features: plan.features,
      mostPopular: plan.id === 'pro', // Mark the Pro plan as most popular
    }));

    return NextResponse.json(formattedPlans);
  } catch (error) {
    console.error('Error fetching plans:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
