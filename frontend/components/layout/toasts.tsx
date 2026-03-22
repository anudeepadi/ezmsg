'use client';

import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

export function Toasts() {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            'flex items-start gap-3 p-4 rounded-lg shadow-elevated animate-fade-in min-w-[300px] max-w-md',
            {
              'bg-success-light border border-success/20': toast.type === 'success',
              'bg-error-light border border-error/20': toast.type === 'error',
              'bg-warning-light border border-warning/20': toast.type === 'warning',
              'bg-surface border border-border': toast.type === 'info',
            }
          )}
        >
          {toast.type === 'success' && (
            <CheckCircle className="h-5 w-5 text-success flex-shrink-0" />
          )}
          {toast.type === 'error' && (
            <AlertCircle className="h-5 w-5 text-error flex-shrink-0" />
          )}
          {toast.type === 'warning' && (
            <AlertTriangle className="h-5 w-5 text-warning flex-shrink-0" />
          )}
          {toast.type === 'info' && (
            <Info className="h-5 w-5 text-accent flex-shrink-0" />
          )}

          <p
            className={cn('flex-1 text-body-sm', {
              'text-success': toast.type === 'success',
              'text-error': toast.type === 'error',
              'text-warning': toast.type === 'warning',
              'text-text': toast.type === 'info',
            })}
          >
            {toast.message}
          </p>

          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 text-text-muted hover:text-text transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
