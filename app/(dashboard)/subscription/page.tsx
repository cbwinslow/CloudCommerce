'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { loadStripe } from '@stripe/stripe-js';
import { SubscriptionPlan, PlanCard } from './components/PlanCard';
import { BillingHistory } from './components/BillingHistory';
import { CurrentPlan } from './components/CurrentPlan';

// Make sure to call `loadStripe` outside of a component's render to avoid
// recreating the `Stripe` object on every render.
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

export default function SubscriptionPage() {
  const { user } = useUser();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [currentPlan, setCurrentPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [billingHistory, setBillingHistory] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'plans' | 'billing'>('plans');

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch available plans
        const plansRes = await fetch('/api/subscription/plans');
        const plansData = await plansRes.json();
        setPlans(plansData);

        // Fetch current subscription
        const subRes = await fetch('/api/subscription');
        const subData = await subRes.json();
        setCurrentPlan(subData);

        // Fetch billing history
        const historyRes = await fetch('/api/billing/history');
        const historyData = await historyRes.json();
        setBillingHistory(historyData);
      } catch (error) {
        console.error('Error fetching subscription data:', error);
      } finally {
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
      const response = await fetch('/api/subscription/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ planId }),
      });
      
      const session = await response.json();
      
      // Redirect to Stripe Checkout
      const stripe = await stripePromise;
      const { error } = await stripe!.redirectToCheckout({
        sessionId: session.id,
      });
      
      if (error) {
        console.error('Error redirecting to checkout:', error);
      }
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
        await fetch('/api/subscription/cancel', {
          method: 'POST',
        });
        
        // Refresh subscription data
        const res = await fetch('/api/subscription');
        const data = await res.json();
        setCurrentPlan(data);
      } catch (error) {
        console.error('Error canceling subscription:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Subscription Management</h1>
      
      {currentPlan && (
        <div className="mb-8">
          <CurrentPlan 
            currentPlan={currentPlan} 
            onCancel={handleCancelSubscription} 
          />
        </div>
      )}

      <div className="border-b border-gray-200 mb-8">
        <nav className="flex -mb-px">
          <button
            onClick={() => setActiveTab('plans')}
            className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'plans'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Change Plan
          </button>
          <button
            onClick={() => setActiveTab('billing')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'billing'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Billing History
          </button>
        </nav>
      </div>

      {activeTab === 'plans' ? (
        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              currentPlanId={currentPlan?.plan?.id}
              onSubscribe={handleSubscribe}
              loading={loading}
            />
          ))}
        </div>
      ) : (
        <BillingHistory history={billingHistory} />
      )}
    </div>
  );
}
