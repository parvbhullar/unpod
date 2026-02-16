'use client';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@unpod/providers';
import SignIn from '@/modules/auth/Signin';
import { useEffect } from 'react';
import AppLoader from '@unpod/components/common/AppLoader';

const Dashboard = () => {
  const router = useRouter();
  const { isAuthenticated, user, isLoading } = useAuthContext();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user?.active_space?.slug) {
      // Logged in - redirect to chat
      router.replace(`/spaces/${user.active_space.slug}/call/`);
    }
  }, [isAuthenticated, user, isLoading]);

  if (isLoading) {
    return <AppLoader />;
  }
  return <SignIn />;
};

export default Dashboard;
