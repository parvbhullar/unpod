import dynamic from 'next/dynamic';
import type { LayoutProps } from '@/types/common';

const AuthLayout = dynamic(() => import('../../core/AppLayout/AuthLayout'));

export default function Layout({ children }: LayoutProps) {
  return <AuthLayout>{children}</AuthLayout>;
}
