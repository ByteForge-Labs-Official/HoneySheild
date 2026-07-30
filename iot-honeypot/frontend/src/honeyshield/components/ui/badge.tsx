import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider transition-colors',
  {
    variants: {
      variant: {
        default: 'border-[#00BFFF]/40 bg-[#00BFFF]/10 text-[#00BFFF]',
        success: 'border-[#00FF88]/40 bg-[#00FF88]/10 text-[#00FF88]',
        warning: 'border-[#FFD600]/40 bg-[#FFD600]/10 text-[#FFD600]',
        danger: 'border-[#FF3D6E]/40 bg-[#FF3D6E]/10 text-[#FF3D6E]',
        outline: 'border-[#1F2A44] text-[#8A9BB8]',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}