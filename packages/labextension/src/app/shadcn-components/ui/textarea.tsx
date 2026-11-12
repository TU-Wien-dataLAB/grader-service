import * as React from 'react';

import { cn } from '../../lib/utils';

function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'flex field-sizing-content min-h-20 self-stretch items-start rounded-xs border border-border bg-input px-2.5 py-2 text-base transition-colors outline-none placeholder:text-muted-foreground active:border-primary focus-visible:ring-primary focus-visible:ring-2 focus-visible:ring-offset-2 focus:ring-primary focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40',
        className
      )}
      {...props}
    />
  );
}

export { Textarea };
