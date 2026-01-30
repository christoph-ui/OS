'use client';

import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, icon, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              'w-full px-3.5 py-2.5 bg-white border rounded-lg text-gray-900',
              'placeholder:text-gray-400 transition-all duration-150',
              'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
              error 
                ? 'border-error-500 focus:ring-error-500/20 focus:border-error-500' 
                : 'border-gray-200 hover:border-gray-300',
              icon && 'pl-10',
              className
            )}
            {...props}
          />
        </div>
        {(error || hint) && (
          <p className={cn(
            'mt-1.5 text-sm',
            error ? 'text-error-500' : 'text-gray-500'
          )}>
            {error || hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
