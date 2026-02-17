import dynamic from 'next/dynamic';
import {SEOdata} from '@/app/SEOData';

const AILanding = dynamic(() => import('../../modules/landing/AI'), {
  loading: () => null,
});

export const metadata =
  SEOdata[(process.env.productId ?? 'unpod.ai') as keyof typeof SEOdata] ??
  SEOdata['unpod.ai'];

export default function HomePage() {
  return <AILanding />;
}
