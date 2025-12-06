"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

/**
 * Providers component that wraps the app with TanStack Query.
 * This must be a client component to use React hooks.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Stale time: data is considered fresh for 5 minutes
            staleTime: 1000 * 60 * 5,
            // Cache time: keep unused data in cache for 10 minutes
            gcTime: 1000 * 60 * 10,
            // Retry failed requests once
            retry: 1,
            // Refetch on window focus in development only
            refetchOnWindowFocus: process.env.NODE_ENV === "development",
          },
          mutations: {
            // Retry failed mutations once
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

