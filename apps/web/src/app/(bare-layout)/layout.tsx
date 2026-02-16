import { Montserrat } from 'next/font/google';
import type { LayoutProps } from '@/types/common';

const montserrat = Montserrat({
  subsets: ['latin'],
  weight: ['700', '800', '900'],
  display: 'swap',
  variable: '--font-montserrat',
});

export default function Layout({ children }: LayoutProps) {
  return <div className={montserrat.variable}>{children}</div>;
}
