'use client';
import React, { Fragment } from 'react';

import HeroSection from './sections/HeroSection';

import LighteningFastIntegration from './sections/LightningFastIntegration';

import InnovationSection from './sections/InnovationSection';
import CallAction from './sections/CallAction';
import VoiceBridge from './sections/VoiceBridge';

import Platforms from './sections/Platforms';
import CustomerLogos from '@/modules/landing/AI/sections/CustomerLogos';

const SIP = () => {
  return (
    <Fragment>
      <HeroSection />
      <CustomerLogos />
      <LighteningFastIntegration />
      <Platforms />
      {/*<FeatureGrid />*/}
      <VoiceBridge />
      <InnovationSection />
      {/*<DeveloperSection />*/}
      <CallAction />
    </Fragment>
  );
};

export default SIP;
