import React from 'react';
import { Outlet } from 'react-router';
import { TooltipProvider } from './shadcn-components/ui/tooltip';
import { SidebarProvider } from './shadcn-components/ui/sidebar';
import { GlobalSidebar } from './components/ui/global-sidebar';

export const Root = () => {
  return (
    <SidebarProvider className={'h-full'}>
      <TooltipProvider>
        <div className={'flex flex-row w-full'}>
          <GlobalSidebar />
          <div className={'@container w-full'}>
            <Outlet />
          </div>
        </div>
      </TooltipProvider>
    </SidebarProvider>
  );
};
