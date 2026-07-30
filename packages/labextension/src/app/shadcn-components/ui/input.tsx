import * as React from 'react';
import { Input as InputPrimitive } from '@base-ui/react/input';

import { cn } from '../../lib/utils';

function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        'h-8 flex flex-col items-center gap-0.5 w-full min-w-0 rounded-xs bg-input px-2 py-1.5 text-base transition-colors border border-border outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 focus:ring-primary focus:ring-2 focus:ring-offset-2 active:border-primary',
        className
      )}
      {...props}
    />
  );
}

export { Input };
