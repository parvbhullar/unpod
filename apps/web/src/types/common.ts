import type { ReactNode } from 'react';

export type SearchParams = Record<string, string | string[] | undefined>;

export type PageProps<
  TParams extends Record<string, string> = Record<string, string>,
> = {
  params: Promise<TParams>;
  searchParams?: Promise<SearchParams>;
};

export type LayoutProps = {
  children: ReactNode;
};

export type ErrorBoundaryProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export type ApiResponse<T = unknown> = {
  data?: T;
  message?: string;
  status?: number;
  error?: string;
};
