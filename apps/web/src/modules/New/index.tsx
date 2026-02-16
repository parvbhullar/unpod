import React from 'react';
import SectionAINetwork from './sections/SectionAINetwork';
import { Flex } from 'antd';
import CTASection from './sections/CTASection';
import SectionHowItWorks from './sections/SectionHowItWorks';
import HeroSection from './sections/HeroSection';
import AiShowcase from './sections/AIShowcase';
import IdentityMarketplace from './sections/IdentityMarketplace';

const VoiceAi = () => {
  return (
    <Flex vertical>
      <HeroSection />
      <SectionAINetwork />
      <SectionHowItWorks />
      <AiShowcase />
      <IdentityMarketplace />
      <CTASection />
    </Flex>
  );
};

export default VoiceAi;
