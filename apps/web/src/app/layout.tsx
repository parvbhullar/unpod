import { Be_Vietnam_Pro } from 'next/font/google';
import { GoogleAnalytics, GoogleTagManager } from '@next/third-parties/google';
import { StyledComponentsRegistry } from './registry';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import 'katex/dist/katex.min.css';
import './reset.css';
import 'simplebar-react/dist/simplebar.min.css';
import AppProviders from '../core/AppProviders';
import { SEOdata } from '@/app/SEOData';
import Script from 'next/script';
import type { LayoutProps } from '@/types/common';

const productId = (process.env.productId ?? 'unpod.ai') as keyof typeof SEOdata;
export const metadata = SEOdata[productId] ?? SEOdata['unpod.ai'];

const beVietnamPro = Be_Vietnam_Pro({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-be-vietnam',
  preload: true,
  adjustFontFallback: true,
});

const gtmId = process.env.GATagId;
const gaId = process.env.GATagId;

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html lang="en" className={beVietnamPro.className} data-scroll-behavior="smooth">
      <head>
        {/* Preconnect to critical third-party origins */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link rel="preconnect" href="https://res.cloudinary.com" />
        {process.env.NODE_ENV !== 'development' &&
          process.env.noIndex !== 'yes' && (
            <>
              <link rel="preconnect" href="https://www.googletagmanager.com" />
              <link rel="dns-prefetch" href="https://www.clarity.ms" />
              <link
                rel="dns-prefetch"
                href="https://www.google-analytics.com"
              />
            </>
          )}
      </head>
      <body>
        <AntdRegistry>
          <StyledComponentsRegistry>
            <AppProviders>{children}</AppProviders>
          </StyledComponentsRegistry>
        </AntdRegistry>

        {/* Load analytics scripts after page becomes interactive - reduces TBT */}
        {process.env.NODE_ENV !== 'development' &&
          process.env.noIndex !== 'yes' && (
            <>
              <Script id="microsoft-clarity" strategy="lazyOnload">
                {`
                (function(c,l,a,r,i,t,y){
                  c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                  t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                  y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
                })(window, document, "clarity", "script", "${process.env.ClarityProjectId}");
              `}
              </Script>

              {/* GTM and GA loaded with worker strategy for better performance */}
              {gtmId ? (
                <GoogleTagManager
                  gtmId={gtmId}
                  gtmScriptUrl="https://www.googletagmanager.com/gtm.js"
                />
              ) : null}
              {gaId ? <GoogleAnalytics gaId={gaId} /> : null}
            </>
          )}
      </body>
    </html>
  );
}
