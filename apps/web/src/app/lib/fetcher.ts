import { redirect } from 'next/navigation';
import { getTokenWithHandle, removeToken } from './session';
import { isRequestSuccessful } from '@unpod/helpers/ApiHelper';
import type { ApiResponse } from '@/types/common';

type FetcherOptions = RequestInit & { headers?: Record<string, string> };

type ApiResponseWithStatus<T> = ApiResponse<T> & {
  status_code?: number;
};

export async function serverFetcher<T = unknown>(
  endpoint: string,
  options: FetcherOptions = {},
  cache: RequestCache = 'no-store',
): Promise<T> {
  const { token, handle } = await getTokenWithHandle();
  const baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (process.env.productId) {
    baseHeaders['Product-Id'] = process.env.productId;
  }
  if (token) {
    baseHeaders.Authorization = `JWT ${token}`;
  }
  if (handle) {
    baseHeaders['org-handle'] = handle;
  }

  const mergedHeaders = {
    ...baseHeaders,
    ...(options.headers ?? {}),
  };

  const baseUrl = process.env.serverApiUrl || process.env.apiUrl;
  const res = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers: mergedHeaders,
    cache,
  });

  console.log(`Requesting URL: ${process.env.apiUrl}${endpoint}`, options, res);

  // Handle 401 Unauthorized - clear cookies and redirect to signin
  if (res.status === 401) {
    await removeToken(); // Clear the invalid token
    redirect('/auth/signin');
  }

  const response = (await res.json()) as ApiResponseWithStatus<T>;
  if (isRequestSuccessful(response.status_code ?? 0)) {
    //console.log(`Fetching URL: ${endpoint}`, response.data, options);
    return response.data as T;
  } else {
    console.log(
      `Error fetching URL: ${process.env.apiUrl}${endpoint}`,
      response,
      options,
    ); /*
    throw new Error(
      `Error fetching data: ${response.message || 'Unknown error'}`
    );*/
    return response.data as T;
  }
}
