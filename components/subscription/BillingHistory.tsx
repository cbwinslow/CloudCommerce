import { format } from 'date-fns';
import { Download, FileText, Receipt } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface BillingRecord {
  id: string;
  date: string | number | Date;
  description: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  receiptUrl?: string;
}

interface BillingHistoryProps {
  history: BillingRecord[];
  loading?: boolean;
}

export function BillingHistory({ history, loading }: BillingHistoryProps) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-gray-100 dark:bg-gray-800 rounded-lg"></div>
        ))}
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/50 mb-4">
          <Receipt className="h-6 w-6 text-purple-600 dark:text-purple-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">No billing history</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Your billing history will appear here once you make a purchase.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden border border-gray-200 dark:border-gray-800 rounded-xl">
      <ul className="divide-y divide-gray-200 dark:divide-gray-800">
        {history.map((record) => (
          <li key={record.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {record.description}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {format(new Date(record.date), 'MMM d, yyyy')}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className={cn(
                  "text-sm font-medium",
                  record.status === 'paid' ? 'text-green-600 dark:text-green-400' :
                  record.status === 'pending' ? 'text-amber-600 dark:text-amber-400' :
                  'text-red-600 dark:text-red-400'
                )}>
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                  }).format(record.amount / 100)}
                </span>
                {record.receiptUrl && (
                  <a
                    href={record.receiptUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:text-purple-500 dark:text-purple-400 dark:hover:text-purple-300"
                  >
                    <span className="sr-only">Download receipt</span>
                    <Download className="h-5 w-5" />
                  </a>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
