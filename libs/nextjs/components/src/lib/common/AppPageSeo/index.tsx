// import React from 'react';
// import PropTypes from 'prop-types';
// import { NextSeo } from 'next-seo';
// import { usePathname, useSearchParams } from 'next/navigation';
// import { queryStringToJSON } from '@unpod/helpers/UrlHelper';
// import { SITE_TITLE, SITE_URL } from '@unpod/constants';
// import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
//
// export const config = { amp: 'hybrid' };
//
// const defaultSeo = {
//   image: `${SITE_URL}/images/landing/connector-image.png`,
//   description:
//     'Unpod.dev is a Low-Code LLM platform designed to automate complex and mundane tasks for organisations. We provide in-house AI assistants (Pilots) to efficiently handle routine tasks at a faster pace, along with support for both open and closed LLM models such as GPT4, Mixtral, and LLAMA.',
//   keywords:
//     'GEN AI, co-pilot, AI-agents, AI Platform, Startups, Get things done, automation, openai, gpt4, llama2, llama1, mid journey, prompt engineering, LLMs, Prompts, digital brain, knowledgebase, organization brain, task execution',
// };
//
// const AppPageSeo = ({
//   seoTitle,
//   seoDesc,
//   keywords,
//   author,
//   copyright,
//   seoImage,
// }) => {
//   const pathname = usePathname();
//   const searchParams = useSearchParams();
//   console.log(`AppPageSeo: asPath: ${pathname}: ${searchParams}`);
//   let canonicalUrl = SITE_URL + pathname;
//
//
//   const images = [];
//
//   if (seoImage) {
//     images.push({
//       url: seoImage?.url,
//     });
//   } else {
//     images.push({ url: defaultSeo.image });
//   }
//
//   const additionalMeta = [
//     {
//       name: 'keywords',
//       content: keywords || defaultSeo.keywords,
//     },
//   ];
//
//   if (author) {
//     additionalMeta.push({
//       name: 'author',
//       content: author,
//     });
//   }
//
//   if (copyright) {
//     additionalMeta.push({
//       name: 'copyright',
//       content: copyright,
//     });
//   }
//
//   const theDescription = getStringFromHtml(seoDesc);
//
//   return (
//     <NextSeo
//       noindex={process.env.noIndex === 'yes'}
//       nofollow={process.env.noFollow === 'yes'}
//       robotsProps={{
//         maxSnippet: -1,
//         maxImagePreview: 'large',
//         maxVideoPreview: -1,
//       }}
//       title={seoTitle}
//       description={(theDescription || defaultSeo.description).substring(
//         0,
//         155
//       )}
//       titleTemplate={seoTitle.length > 42 ? '' : `%s - ${SITE_TITLE}`}
//       additionalMetaTags={additionalMeta}
//       canonical={canonicalUrl}
//       openGraph={{
//         url: SITE_URL + pathname,
//         type: 'website',
//         title: `${seoTitle} - ${SITE_TITLE}`,
//         description: theDescription,
//         siteName: SITE_TITLE,
//         images,
//       }}
//       twitter={{
//         cardType: 'summary_large_image',
//         site: SITE_TITLE,
//         // handle: '@unpod',
//       }}
//     />
//   );
// };
//
// AppPageSeo.propTypes = {
//   seoTitle: PropTypes.string,
//   seoDesc: PropTypes.string,
//   keywords: PropTypes.string,
//   author: PropTypes.string,
//   copyright: PropTypes.string,
//   seoImage: PropTypes.object,
// };
//
// AppPageSeo.defaultProps = {
//   seoTitle: 'Home',
// };
//
// export default AppPageSeo;
import React from 'react';

const AppPageSeo = () => {
  return <></>;
};

export default AppPageSeo;
