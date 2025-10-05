import React from 'react';

interface CurrentPlanProps {
  currentPlan: {
    plan: {
      id: string;
      name: string;
      monthly_listings: number;
      features: string[];
    };
    status: string;
    current_period_end?: string;
    usage: {
      current: number;
      limit: number;
      remaining: number;
    };
  };
  onCancel: () => void;
}

export function CurrentPlan({ currentPlan, onCancel }: CurrentPlanProps) {
  const isCancelled = currentPlan.status === 'cancelled';
  const isFreePlan = currentPlan.plan.id === 'free';
  const usagePercentage = Math.min(
    100,
    (currentPlan.usage.current / (currentPlan.usage.limit || 1)) * 100
  );

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          Your Current Plan: {currentPlan.plan.name}
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          {isCancelled
            ? 'Your subscription will end on ' +
              new Date(currentPlan.current_period_end || '').toLocaleDateString()
            : isFreePlan
            ? 'Upgrade to unlock more features and capabilities.'
            : `Your subscription renews on ${new Date(
                currentPlan.current_period_end || ''
              ).toLocaleDateString()}.`}
        </p>
      </div>
      <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
        <dl className="sm:divide-y sm:divide-gray-200">
          <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  isCancelled
                    ? 'bg-yellow-100 text-yellow-800'
                    : currentPlan.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {currentPlan.status.charAt(0).toUpperCase() + currentPlan.status.slice(1)}
              </span>
            </dd>
          </div>
          <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Monthly Listings</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              {currentPlan.usage.limit === 0 ? 'Unlimited' : currentPlan.usage.limit} listings/month
            </dd>
          </div>
          {!isFreePlan && (
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Usage this month</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${
                      usagePercentage > 90 ? 'bg-red-600' : 'bg-blue-600'
                    }`}
                    style={{ width: `${usagePercentage}%` }}
                  ></div>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  {currentPlan.usage.current} of{' '}
                  {currentPlan.usage.limit === 0 ? 'unlimited' : currentPlan.usage.limit} listings used
                  ({Math.round(usagePercentage)}%)
                </p>
              </dd>
            </div>
          )}
          <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-500">Plan Features</dt>
            <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
              <ul className="list-disc pl-5 space-y-1">
                {currentPlan.plan.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </dd>
          </div>
        </dl>
      </div>
      <div className="px-4 py-4 bg-gray-50 text-right sm:px-6">
        {!isFreePlan && (
          <button
            onClick={onCancel}
            disabled={isCancelled}
            className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${
              isCancelled
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
            }`}
          >
            {isCancelled ? 'Cancellation Pending' : 'Cancel Subscription'}
          </button>
        )}
      </div>
    </div>
  );
}
