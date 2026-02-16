'use client';
import React, { Fragment } from 'react';
import { StyledSubTitle, StyledTitle } from './index.styled';

import SectionHeader from './sections/SectionHeader';

import SectionHeroImage from '../../common/SectionHeroImage';

import SectionHowItWorks from './sections/SectionHowItWorks';

// const SectionSolvesProblems = dynamic(
//   () => import('./sections/SectionSolvesProblems'),
//   {
//     ssr: false,
//   }
// );
import CTASection from '@/modules/New/sections/CTASection';
import { useIntl } from 'react-intl';
/*const SectionAppsLogo = dynamic(() => import('./sections/SectionAppsLogo'));

const SectionImageInfo = dynamic(() => import('../common/SectionImageInfo'));

const AppAgentsBanner = dynamic(
  () => import('@unpod/components/AppAgentsBanner')
);*/

const Landing = () => {
  const { formatMessage } = useIntl();
  return (
    <Fragment>
      <SectionHeader />
      {/*<CustomerLogos/>*/}
      {/*<SectionLeadsConversation />*/}
      <SectionHowItWorks />
      <SectionHeroImage
        heading={
          <StyledTitle level={2}>
            {formatMessage({ id: 'aiHero.heading1' })}{' '}
            <span className="text-active">
              {formatMessage({ id: 'aiHero.headingActive1' })}
            </span>{' '}
            {formatMessage({ id: 'aiHero.heading2' })}{' '}
            <span className="text-active">
              {formatMessage({ id: 'aiHero.headingActive2' })}
            </span>
          </StyledTitle>
        }
        subHeading={
          <StyledSubTitle level={3}>
            {formatMessage({ id: 'aiHero.subHeading' })}
          </StyledSubTitle>
        }
        headerMaxWidth={720}
      />

      {/* <SectionSolvesProblems /> */}
      {/* <SectionContactUs />*/}
      <CTASection />

      {/*<SectionImageInfo data={landing.privacy} />
      <SectionImageInfo data={landing.privacy} textPosition="right" />*/}

      {/*<SectionAppsLogo {...landing.connectors} />

      <AppPageSection bgColor="#fff">
        <AppAgentsBanner />
      </AppPageSection>*/}
    </Fragment>
  );
};

export default Landing;
