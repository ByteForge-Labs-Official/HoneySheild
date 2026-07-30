import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'relative bg-gradient-to-br from-[#00BFFF] via-[#00E5FF] to-[#00FF88] text-[#001018] shadow-[0_0_24px_rgba(0,191,255,0.45)] hover:shadow-[0_0_36px_rgba(0,229,255,0.7)] hover:-translate-y-0.5',
        outline:
          'border border-[#00BFFF]/40 bg-transparent text-[#E6F1FF] hover:border-[#00E5FF] hover:bg-[#00BFFF]/10 hover:shadow-[0_0_18px_rgba(0,191,255,0.25)]',
        ghost:
          'bg-transparent text-[#E6F1FF] hover:bg-[#00BFFF]/10',
        secondary:
          'bg-[#0F1626] border border-[#1F2A44] text-[#E6F1FF] hover:border-[#00BFFF]/50',
        danger:
          'bg-[#FF3D6E]/15 border border-[#FF3D6E]/50 text-[#FF3D6E] hover:bg-[#FF3D6E]/25',
      },
      size: {
        default: 'h-10 px-5 py-2',
        sm: 'h-8 px-3 text-xs',
        lg: 'h-12 px-7 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };