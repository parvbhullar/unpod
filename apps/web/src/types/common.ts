export type RouteParams<
  T extends Record<string, string> = Record<string, string>,
> = {
  params: T;
};

export type SearchParams = Record<string, string | string[] | undefined>;

export type PageProps<
  TParams extends Record<string, string> = Record<string, string>,
> = {
  params: TParams;
  searchParams?: SearchParams;
};

import type { ReactNode } from 'react';

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
  [key: string]: unknown;
};

export type Nullable<T> = T | null;
