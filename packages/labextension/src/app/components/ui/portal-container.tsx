import * as React from 'react';
import { cn } from '../../lib/utils';

export const PortalContainerContext = React.createContext<HTMLElement | null>(
  null
);
export const usePortalContainer = () =>
  React.useContext(PortalContainerContext);

export function PortalContainer({
  children,
  className
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const [container, setContainer] = React.useState<HTMLElement | null>(null);
  return (
    <div
      ref={setContainer}
      className={cn('relative h-full w-full overflow-hidden', className)}
    >
      <PortalContainerContext.Provider value={container}>
        {children}
      </PortalContainerContext.Provider>
    </div>
  );
}
