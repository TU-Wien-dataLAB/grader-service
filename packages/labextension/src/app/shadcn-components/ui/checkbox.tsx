'use client';

import { CheckIcon, MinusIcon } from 'lucide-react';
import { Checkbox as CheckboxPrimitive } from 'radix-ui';
import * as React from 'react';
import { cn } from '../../lib/utils';

// Replace the `Checkbox` component in `@components/ui/checkbox` with below component and use it here to support indeterminate.
const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    className={cn(
      'group peer h-4 w-4 shrink-0 rounded-xs border border-border focus-visible:ring-primary focus-visible:ring-2 focus-visible:ring-offset-1 focus:ring-offset-1 focus:ring-primary focus:ring-2 disabled:cursor-not-allowed disabled:bg-background data-[state=checked]:bg-primary data-[state=indeterminate]:bg-primary data-[state=checked]:text-primary-foreground data-[state=indeterminate]:text-primary-foreground data-[state=checked]:hover:bg-primary-hover data-[state=checked]:active:bg-primary-hover data-[state=indeterminate]:active:bg-primary-hover data-[state=indeterminate]:hover:bg-primary-hover',
      className
    )}
    ref={ref}
    {...props}
  >
    <CheckboxPrimitive.Indicator
      className={cn('flex items-center justify-center text-current')}
    >
      <MinusIcon className="hidden h-4 w-4 group-data-[state=indeterminate]:block" />
      <CheckIcon className="hidden h-4 w-4 group-data-[state=checked]:block" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
