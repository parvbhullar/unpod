'use client';

import { useLayoutEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@unpod/providers';
import { desktopAPI } from '@/helpers/desktopNotifications';
import dynamic from 'next/dynamic';

const SIPLanding = dynamic(() => import('../../modules/landing/SIP'), {
  loading: () => null,
});
const AILanding = dynamic(() => import('../../modules/landing/AI'), {
  loading: () => null,
});

const HomePageClient = () => {
  const router = useRouter();
  const { isAuthenticated, user, isLoading } = useAuthContext();

  useLayoutEffect(() => {
    // Check if running in desktop app (Tauri )
    const isDesktop = desktopAPI.isDesktop();

    // Only handle desktop redirect for unpod.ai
    if (isDesktop && process.env.productId === 'unpod.ai' && !isLoading) {
      if (isAuthenticated && user?.active_space?.slug) {
        // Logged in - redirect to chat
        router.replace(`/spaces/${user.active_space.slug}/call/`);
      } else if (!isAuthenticated) {
        // Not logged in - redirect to signin
        router.replace('/auth/signin');
      }
    }
  }, [isAuthenticated, user, isLoading, router]);

  // Check if running in desktop app for initial render
  const isDesktop = desktopAPI.isDesktop();

  // For desktop app, show nothing while redirecting
  if (isDesktop && process.env.productId === 'unpod.ai') {
    return null;
  }

  // Normal web view - show landing page
  return process.env.productId === 'unpod.dev' ? <SIPLanding /> : <AILanding />;
};

export default HomePageClient;
