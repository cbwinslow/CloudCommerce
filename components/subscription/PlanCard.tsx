import { Button } from "@/components/ui/button";
import { Check, Zap, Sparkles, Rocket } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  interval: string;
  features: string[];
  isPopular?: boolean;
  isCurrent?: boolean;
}

interface PlanCardProps {
  plan: SubscriptionPlan;
  isCurrent?: boolean;
  onSelect: (planId: string) => void;
  loading?: boolean;
}

export function PlanCard({ plan, isCurrent, onSelect, loading }: PlanCardProps) {
  const price = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(plan.price / 100);

  const getPlanIcon = () => {
    switch (plan.name.toLowerCase()) {
      case 'starter':
        return <Zap className="w-5 h-5" />;
      case 'pro':
        return <Rocket className="w-5 h-5" />;
      case 'enterprise':
        return <Sparkles className="w-5 h-5" />;
      default:
        return null;
    }
  };

  return (
    <div
      className={cn(
        "relative flex flex-col p-6 rounded-2xl border-2 transition-all duration-200",
        isCurrent
          ? "border-purple-500 bg-gradient-to-br from-purple-50 to-white dark:from-purple-900/20 dark:to-gray-900"
          : "border-gray-200 dark:border-gray-800 hover:border-purple-300 dark:hover:border-purple-700/70 hover:shadow-lg",
        plan.isPopular ? "border-2 border-purple-500 shadow-lg" : ""
      )}
    >
      {plan.isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
          Most Popular
        </div>
      )}
      
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            {getPlanIcon()}
            {plan.name}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {plan.description}
          </p>
        </div>
        
        <div className="text-right">
          <span className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-500 bg-clip-text text-transparent">
            {price}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            /{plan.interval}
          </span>
        </div>
      </div>

      <div className="flex-1 space-y-3 mb-6">
        {plan.features.map((feature, index) => (
          <div key={index} className="flex items-start">
            <Check className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5 mr-2" />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {feature}
            </span>
          </div>
        ))}
      </div>

      <Button
        onClick={() => onSelect(plan.id)}
        disabled={isCurrent || loading}
        className={cn(
          "w-full mt-auto transition-all duration-200",
          isCurrent
            ? "bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600"
            : "bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-700 hover:to-blue-600",
          plan.isPopular && "shadow-lg shadow-purple-500/20"
        )}
        size="lg"
      >
        {isCurrent ? 'Current Plan' : 'Choose Plan'}
      </Button>
    </div>
  );
}
