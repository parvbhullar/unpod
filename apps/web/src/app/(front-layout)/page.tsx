import dynamic from 'next/dynamic';
import { SEOdata } from '@/app/SEOData';

const SIPLanding = dynamic(() => import('../../modules/landing/SIP'), {
  loading: () => null,
});
const AILanding = dynamic(() => import('../../modules/landing/AI'), {
  loading: () => null,
});

export const metadata =
  SEOdata[(process.env.productId ?? 'unpod.ai') as keyof typeof SEOdata] ??
  SEOdata['unpod.ai'];

export default function HomePage() {
  return process.env.productId === 'unpod.dev' ? <SIPLanding /> : <AILanding />;
}
