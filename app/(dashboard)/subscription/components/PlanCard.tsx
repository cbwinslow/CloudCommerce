import React from 'react';

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  monthly_listings: number;
  price_monthly: number;
  price_yearly?: number;
  features: string[];
  mostPopular?: boolean;
}

interface PlanCardProps {
  plan: SubscriptionPlan;
  currentPlanId?: string;
  onSubscribe: (planId: string) => void;
  loading: boolean;
}

export function PlanCard({ plan, currentPlanId, onSubscribe, loading }: PlanCardProps) {
  const isCurrentPlan = plan.id === currentPlanId;
  const isFreePlan = plan.id === 'free';
  const isYearly = plan.price_yearly !== undefined && plan.price_yearly > 0;

  return (
    <div
      className={`relative flex flex-col p-6 bg-white rounded-lg border ${
        plan.mostPopular ? 'border-blue-500' : 'border-gray-200'
      }`}
    >
      {plan.mostPopular && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span className="bg-blue-500 text-white text-xs font-medium px-3 py-1 rounded-full">
            Most Popular
          </span>
        </div>
      )}

      <h3 className="text-lg font-medium text-gray-900">{plan.name}</h3>
      <p className="mt-2 text-sm text-gray-500">{plan.description}</p>

      <div className="mt-4">
        <span className="text-3xl font-bold text-gray-900">
          ${plan.price_monthly?.toFixed(2)}
        </span>
        <span className="text-base font-medium text-gray-500">/month</span>
        {isYearly && (
          <span className="ml-2 text-sm text-gray-500">
            or ${plan.price_yearly?.toFixed(2)}/year (save 20%)
          </span>
        )}
      </div>

      <ul className="mt-6 space-y-4">
        {plan.features.map((feature, index) => (
          <li key={index} className="flex items-start">
            <svg
              className="h-5 w-5 text-green-500 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span className="text-sm text-gray-700">{feature}</span>
          </li>
        ))}
      </ul>

      <div className="mt-8">
        {isCurrentPlan ? (
          <button
            disabled
            className="w-full px-4 py-2 text-sm font-medium text-white bg-gray-400 rounded-md cursor-not-allowed"
          >
            Current Plan
          </button>
        ) : (
          <button
            onClick={() => onSubscribe(plan.id)}
            disabled={loading || isFreePlan}
            className={`w-full px-4 py-2 text-sm font-medium text-white rounded-md ${
              isFreePlan
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Processing...' : isFreePlan ? 'Current Plan' : 'Upgrade'}
          </button>
        )}
      </div>
    </div>
  );
}
