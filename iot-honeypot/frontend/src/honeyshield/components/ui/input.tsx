import * as React from 'react';
import { cn } from '../../lib/utils';

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        'flex h-10 w-full rounded-md border border-[#1F2A44] bg-[#0F1626]/80 px-3 py-2 text-sm text-[#E6F1FF] placeholder:text-[#8A9BB8] focus-visible:outline-none focus-visible:border-[#00BFFF] focus-visible:shadow-[0_0_12px_rgba(0,191,255,0.35)] disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';