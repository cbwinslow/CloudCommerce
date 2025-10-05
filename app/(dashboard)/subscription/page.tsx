'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { loadStripe } from '@stripe/stripe-js';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlanCard, SubscriptionPlan } from '@/components/subscription/PlanCard';
import { BillingHistory } from '@/components/subscription/BillingHistory';
import { CurrentPlan } from '@/components/subscription/CurrentPlan';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

// Make sure to call `loadStripe` outside of a component's render to avoid
// recreating the `Stripe` object on every render.
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

// Mock data for demonstration
const MOCK_PLANS: SubscriptionPlan[] = [
  {
    id: 'price_starter',
    name: 'Starter',
    description: 'Perfect for individuals getting started',
    price: 990, // $9.99
    interval: 'month',
    features: [
      '10 products',
      'Basic analytics',
      'Email support',
      '1GB storage',
    ],
  },
  {
    id: 'price_pro',
    name: 'Pro',
    description: 'For growing businesses',
    price: 2990, // $29.99
    interval: 'month',
    isPopular: true,
    features: [
      '50 products',
      'Advanced analytics',
      'Priority support',
      '10GB storage',
      'API access',
    ],
  },
  {
    id: 'price_enterprise',
    name: 'Enterprise',
    description: 'For large scale operations',
    price: 9990, // $99.99
    interval: 'month',
    features: [
      'Unlimited products',
      'Advanced analytics',
      '24/7 support',
      '100GB storage',
      'API access',
      'Custom integrations',
    ],
  },
];

export default function SubscriptionPage() {
  const { user } = useUser();
  const [plans, setPlans] = useState<SubscriptionPlan[]>(MOCK_PLANS);
  const [currentPlan, setCurrentPlan] = useState<any>(null);
  const [billingHistory, setBillingHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('plans');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // In a real app, you would fetch this from your API
        // const [plansRes, subRes, historyRes] = await Promise.all([
        //   fetch('/api/subscription/plans'),
        //   fetch('/api/subscription'),
        //   fetch('/api/billing/history'),
        // ]);
        
        // Mock data for now
        setTimeout(() => {
          setPlans(MOCK_PLANS);
          setCurrentPlan({
            id: 'sub_123',
            name: 'Pro',
            status: 'active',
            currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
          });
          setBillingHistory([
            {
              id: 'inv_123',
              date: new Date(),
              description: 'Pro Plan - Monthly',
              amount: 2990,
              status: 'paid',
              receiptUrl: '#'
            },
            {
              id: 'inv_122',
              date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
              description: 'Pro Plan - Monthly',
              amount: 2990,
              status: 'paid',
              receiptUrl: '#'
            },
          ]);
          setLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching subscription data:', error);
        setLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  const handleSubscribe = async (planId: string) => {
    try {
      setLoading(true);
      // In a real app, you would call your API
      // const response = await fetch('/api/subscription/subscribe', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ planId }),
      // });
      // const session = await response.json();
      // const stripe = await stripePromise;
      // await stripe!.redirectToCheckout({ sessionId: session.id });
      
      // Mock success
      alert('Redirecting to checkout...');
    } catch (error) {
      console.error('Error subscribing to plan:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (window.confirm('Are you sure you want to cancel your subscription?')) {
      try {
        setLoading(true);
        // In a real app, you would call your API
        // await fetch('/api/subscription/cancel', { method: 'POST' });
        // const res = await fetch('/api/subscription');
        // setCurrentPlan(await res.json());
        
        // Mock cancellation
        setCurrentPlan({
          ...currentPlan,
          cancelAtPeriodEnd: true,
        });
      } catch (error) {
        console.error('Error canceling subscription:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleResumeSubscription = async () => {
    try {
      setLoading(true);
      // In a real app, you would call your API
      // await fetch('/api/subscription/resume', { method: 'POST' });
      // const res = await fetch('/api/subscription');
      // setCurrentPlan(await res.json());
      
      // Mock resume
      setCurrentPlan({
        ...currentPlan,
        cancelAtPeriodEnd: false,
      });
    } catch (error) {
      console.error('Error resuming subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !plans.length) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          <Skeleton className="h-10 w-64 mb-8" />
          <div className="grid md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="h-[500px]">
                <CardHeader>
                  <Skeleton className="h-6 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-1/2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-1/2 mb-6" />
                  <div className="space-y-3">
                    {[1, 2, 3, 4].map((j) => (
                      <Skeleton key={j} className="h-4 w-full" />
                    ))}
                  </div>
                  <Skeleton className="h-10 w-full mt-8" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent mb-4">
            Your Subscription
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Choose the perfect plan for your business needs or manage your current subscription.
          </p>
        </div>

        <Tabs defaultValue="plans" className="w-full">
          <div className="flex justify-center mb-12">
            <TabsList className="bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
              <TabsTrigger 
                value="plans" 
                className="px-6 py-2 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-purple-600 dark:data-[state=active]:bg-gray-700 dark:data-[state=active]:text-white"
              >
                Plans & Pricing
              </TabsTrigger>
              <TabsTrigger 
                value="billing" 
                className="px-6 py-2 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-purple-600 dark:data-[state=active]:bg-gray-700 dark:data-[state=active]:text-white"
              >
                Billing History
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="plans">
            <div className="space-y-12">
              <CurrentPlan 
                plan={currentPlan} 
                onCancel={handleCancelSubscription}
                onResume={handleResumeSubscription}
                loading={loading}
              />
              
              <div>
                <h2 className="text-2xl font-bold text-center mb-2">
                  Choose Your Plan
                </h2>
                <p className="text-center text-gray-500 dark:text-gray-400 mb-8">
                  Select the plan that best fits your business needs
                </p>
                
                <div className="grid md:grid-cols-3 gap-6">
                  {plans.map((plan) => (
                    <PlanCard
                      key={plan.id}
                      plan={plan}
                      isCurrent={currentPlan?.name === plan.name}
                      onSelect={handleSubscribe}
                      loading={loading}
                    />
                  ))}
                </div>
                
                <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
                  <p>Need a custom plan? <a href="#" className="text-purple-600 hover:underline dark:text-purple-400">Contact our sales team</a></p>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="billing">
            <Card>
              <CardHeader>
                <CardTitle>Billing History</CardTitle>
                <CardDescription>
                  View and download your past invoices and receipts
                </CardDescription>
              </CardHeader>
              <CardContent>
                <BillingHistory history={billingHistory} loading={loading} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
