import { Theme } from '@radix-ui/themes';
import * as React from 'react';
import { useEffect, useState } from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GlobalObjects } from './index';
import '../style/css/index.css';
import { createMemoryRouter, DataRouter, RouterProvider } from 'react-router';
import { getRoutes } from './routes';
import { PortalContainerContext } from './portal-container';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10 * 60 * 1000,
      cacheTime: 15 * 60 * 1000,
      refetchOnReconnect: true
    } as any
  }
});

type StatusState = {
  status: 'success' | 'error' | null;
  message: string | null;
};

type MutationStatusContextType = {
  status: StatusState;
  setStatus: (status: StatusState) => void;
};

const MutationContext = React.createContext<MutationStatusContextType | null>(
  null
);

export function useMutationStatus() {
  const ctx = React.useContext(MutationContext);
  if (!ctx) {
    throw new Error(
      'useMutationStatus must be used within MutationStatusProvider'
    );
  }
  return ctx;
}

function GraderServiceViewComponent({
  theme,
  router,
  parentNode
}: {
  theme: 'dark' | 'light';
  router: DataRouter;
  parentNode: HTMLElement | null;
}) {
  const [status, setStatus] = useState<StatusState>({
    status: null,
    message: null
  });
  const [portalContainer, setPortalContainer] = useState<HTMLElement | null>(
    null
  );

  useEffect(() => {
    if (status.status !== null) {
      const timer = setTimeout(() => {
        setStatus({ status: null, message: null });
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [status]);

  return (
    <QueryClientProvider client={queryClient}>
      <Theme className={theme} style={{ height: '100%' }}>
        <PortalContainerContext.Provider value={portalContainer}>
          <div className="h-full @container">
            <MutationContext.Provider value={{ status, setStatus }}>
              <RouterProvider router={router} />
            </MutationContext.Provider>
          </div>
        </PortalContainerContext.Provider>
        <div
          ref={setPortalContainer}
          style={{ position: 'relative', zIndex: 1000 }}
        />
      </Theme>
    </QueryClientProvider>
  );
}

export class GraderServiceWidget extends ReactWidget {
  theme: 'dark' | 'light';
  router: DataRouter;

  constructor(options: GraderServiceView.IOptions = {}) {
    super();
    this.id = options.id || 'grader-service-view';
    this.addClass('GradingWidget');
    this.router = createMemoryRouter(getRoutes(), { initialEntries: ['/'] });

    const themeManager = GlobalObjects.themeManager;
    const resolveTheme = () =>
      themeManager.isLight(themeManager.theme ?? 'light') ? 'light' : 'dark';

    this.theme = resolveTheme();

    themeManager.themeChanged.connect(() => {
      this.theme = resolveTheme();
      this.update();
    }, this);
  }

  render() {
    return (
      <GraderServiceViewComponent
        theme={this.theme}
        router={this.router}
        parentNode={this.node.parentNode?.parentElement ?? null}
      />
    );
  }
}

export namespace GraderServiceView {
  export interface IOptions {
    id?: string;
  }
}
