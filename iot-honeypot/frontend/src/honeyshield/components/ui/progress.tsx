import * as React from 'react';
import { cn } from '../../lib/utils';

export const Progress = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value: number; tone?: 'cyan' | 'green' | 'red' | 'orange' }
>(({ className, value, tone = 'cyan', ...props }, ref) => {
  const toneClass = {
    cyan: 'from-[#00BFFF] to-[#00E5FF]',
    green: 'from-[#00E5FF] to-[#00FF88]',
    red: 'from-[#FF8A1F] to-[#FF3D6E]',
    orange: 'from-[#FFD600] to-[#FF8A1F]',
  }[tone];
  return (
    <div
      ref={ref}
      className={cn('relative h-1.5 w-full overflow-hidden rounded-full bg-[#1A2238]', className)}
      {...props}
    >
      <div
        className={cn('h-full bg-gradient-to-r transition-all duration-700', toneClass)}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
});
Progress.displayName = 'Progress';