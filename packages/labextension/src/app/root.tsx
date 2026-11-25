import React from 'react';
import { Outlet } from 'react-router';
import { TooltipProvider } from './shadcn-components/ui/tooltip';
import { SidebarProvider } from './shadcn-components/ui/sidebar';
import { GlobalSidebar } from './components/ui/global-sidebar';
import RoutePersist from './components/utils/route-persist';
import { PortalContainer } from './components/ui/portal-container';

export const Root = () => {
  return (
    <PortalContainer>
      <SidebarProvider className={'h-full'}>
        <TooltipProvider>
          <div className={'flex flex-row w-full'}>
            <GlobalSidebar />
            <RoutePersist />
            <div className={'@container w-full'}>
              <Outlet />
            </div>
          </div>
        </TooltipProvider>
      </SidebarProvider>
    </PortalContainer>
  );
};
