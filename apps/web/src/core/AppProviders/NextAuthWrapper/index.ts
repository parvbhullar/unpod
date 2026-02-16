import { serverFetcher } from '@/app/lib/fetcher';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { setAuthToken, setOrgHeader } from '@unpod/services';
import { cloneElement, type ReactElement } from 'react';
import type { User } from '@unpod/constants/types';

type NextAuthWrapperProps = {
  children: ReactElement;
};

const NextAuthWrapper = async ({ children }: NextAuthWrapperProps) => {
  const cookieStore = await cookies();
  const token = cookieStore.get('token')?.value || '';
  let props: Record<string, unknown> = {};
  if (token) {
    try {
      const user = await serverFetcher<User>('auth/me');
      if (user) {
        setOrgHeader(user?.active_organization?.domain_handle);
        setAuthToken(token);
        props = {
          userData: { token, user },
          activeOrg: user?.active_organization,
          isAuthenticate: true,
        };
      } else {
        // No user data returned — redirect to clear cookies via Route Handler
        redirect('/api/auth/clear-session');
      }
    } catch (error: unknown) {
      // auth/me failed — redirect to clear cookies via Route Handler
      const message = error instanceof Error ? error.message : String(error);
      console.error('NextAuthWrapper: Failed to fetch user data', message);
      redirect('/api/auth/clear-session');
    }
  }
  return cloneElement(children, props);
};

export default NextAuthWrapper;
