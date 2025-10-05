import { Button } from "@/components/ui/button";
import { CheckCircle, Clock, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface CurrentPlanProps {
  plan: {
    name: string;
    status: string;
    currentPeriodEnd: string | number | Date;
    cancelAtPeriodEnd?: boolean;
  } | null;
  loading?: boolean;
  onCancel?: () => void;
  onResume?: () => void;
}

export function CurrentPlan({ plan, loading, onCancel, onResume }: CurrentPlanProps) {
  if (loading || !plan) {
    return (
      <div className="animate-pulse space-y-4 p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
        <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-1/3"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2"></div>
        <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded w-1/4"></div>
      </div>
    );
  }

  const isActive = plan.status === 'active';
  const isCanceled = plan.cancelAtPeriodEnd;
  const renewalDate = new Date(plan.currentPeriodEnd);
  
  return (
    <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              {plan.name} Plan
            </h3>
            <span className={cn(
              "ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
              isActive && !isCanceled 
                ? "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300"
                : "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300"
            )}>
              {isCanceled ? "Canceling" : isActive ? "Active" : "Inactive"}
            </span>
          </div>
          
          <div className="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400">
            {isCanceled ? (
              <>
                <AlertTriangle className="flex-shrink-0 mr-1.5 h-5 w-5 text-amber-400" />
                <span>Your subscription will end on {renewalDate.toLocaleDateString()}</span>
              </>
            ) : (
              <>
                <CheckCircle className="flex-shrink-0 mr-1.5 h-5 w-5 text-green-500" />
                <span>Next billing date: {renewalDate.toLocaleDateString()}</span>
              </>
            )}
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          {isActive && !isCanceled && onCancel && (
            <Button 
              variant="outline" 
              onClick={onCancel}
              className="w-full sm:w-auto"
            >
              Cancel Subscription
            </Button>
          )}
          {isCanceled && onResume && (
            <Button 
              variant="default"
              onClick={onResume}
              className="w-full sm:w-auto bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600"
            >
              Resume Subscription
            </Button>
          )}
          <Button 
            variant="outline" 
            className="w-full sm:w-auto"
            onClick={() => {
              // Handle update payment method
              alert('Redirecting to customer portal...');
            }}
          >
            Update Payment
          </Button>
        </div>
      </div>
    </div>
  );
}
```
