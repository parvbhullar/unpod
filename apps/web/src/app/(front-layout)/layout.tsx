import dynamic from 'next/dynamic';
import type { LayoutProps } from '@/types/common';

const FrontendLayout = dynamic(
  () => import('../../core/AppLayout/FrontendLayout'),
);

export default function Layout({ children }: LayoutProps) {
  return (
    <FrontendLayout
      headerBg={
        process.env.productId === 'unpod.dev' ? 'transparent' : undefined
      }
    >
      {children}
    </FrontendLayout>
  );
}
