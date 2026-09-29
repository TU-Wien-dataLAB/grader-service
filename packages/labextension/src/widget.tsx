import { Theme } from '@radix-ui/themes';
import * as React from 'react';
import { useEffect, useState } from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GlobalObjects } from './index';
import '../style/css/index.css';
import { createMemoryRouter, DataRouter, RouterProvider } from 'react-router';
import { getRoutes } from './routes';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10 * 60 * 1000,
      cacheTime: 15 * 60 * 1000
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

const defaultStatus: StatusState = { status: null, message: null };
export const MutationContext =
  React.createContext<MutationStatusContextType | null>(null);

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
  const [status, setStatus] = useState<StatusState>(defaultStatus);

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
        <div className="h-full @container">
          <MutationContext.Provider value={{ status, setStatus }}>
            <RouterProvider router={router} />
          </MutationContext.Provider>
        </div>
      </Theme>
    </QueryClientProvider>
  );
}

export class GraderServiceView extends ReactWidget {
  theme: 'dark' | 'light';
  router: DataRouter;

  constructor(options: CourseManageView.IOptions = {}) {
    super();
    this.id = options.id || 'course-manage-view';
    this.addClass('GradingWidget');
    this.router = createMemoryRouter(getRoutes(), { initialEntries: ['/'] });

    const themeManager = GlobalObjects.themeManager;
    this.theme = themeManager.isLight(themeManager.theme ?? 'light')
      ? 'light'
      : 'dark';

    themeManager.themeChanged.connect(() => {
      this.theme = themeManager.isLight(themeManager.theme ?? 'light')
        ? 'light'
        : 'dark';
      this.update(); // <- tells Lumino to re-invoke render()
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

export namespace CourseManageView {
  export interface IOptions {
    id?: string;
  }
}
