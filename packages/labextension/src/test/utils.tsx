import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router';
import { MutationContext } from '../widget';

export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
        staleTime: Infinity
      }
    }
  });

type StatusState = {
  status: 'success' | 'error' | null;
  message: string | null;
};

interface WrapperOptions {
  preSeededQueries?: Array<{ queryKey: unknown[]; data: unknown }>;
  initialRouteEntries?: string[];
  status?: StatusState;
  setStatus?: jest.Mock | ((status: StatusState) => void);
}

export const createAllProvidersWrapper = (options?: WrapperOptions) => {
  const testQueryClient = createTestQueryClient();

  if (options?.preSeededQueries) {
    options.preSeededQueries.forEach(({ queryKey, data }) => {
      testQueryClient.setQueryData(queryKey, data);
    });
  }

  const contextValue = {
    status: options?.status ?? { status: null, message: null },
    setStatus: options?.setStatus ?? jest.fn()
  };

  return ({ children }: { children: React.ReactNode }) => {
    return (
      <QueryClientProvider client={testQueryClient}>
        <MutationContext.Provider value={contextValue}>
          <MemoryRouter initialEntries={options?.initialRouteEntries || ['/']}>
            <div className="h-full">{children}</div>
          </MemoryRouter>
        </MutationContext.Provider>
      </QueryClientProvider>
    );
  };
};
