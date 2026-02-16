'use client';
import React from 'react';
import {
  StyledLogoWrapper,
  StyledMarquee,
  StyledRoot,
  StyledTrack,
} from './index.styled';
import AppPageSection from '@unpod/components/common/AppPageSection';
import Image from 'next/image';

const logos = [
  '/images/clients-logos/Aajneeti.png',
  '/images/clients-logos/askIITians.png',
  '/images/clients-logos/Astra_AI.png',
  '/images/clients-logos/broki.png',
  '/images/clients-logos/FabricHQ.png',
  '/images/clients-logos/faffit.jpg',
  '/images/clients-logos/Koel.png',
  '/images/clients-logos/LenDenClub.png',
  '/images/clients-logos/PropalAI.jpg',
  '/images/clients-logos/Salk.png',
  '/images/clients-logos/Superdash.png',
  '/images/clients-logos/Voxket.png',
  '/images/clients-logos/Vyantra.png',
  '/images/clients-logos/Zeko.png',
];

const CustomerLogos = () => {
  return (
    <AppPageSection style={{ padding: '20px 0px' }}>
      <StyledRoot>
        <StyledMarquee>
          <StyledTrack>
            {/* double list for perfect seamless loop */}
            {logos.concat(logos).map((src, i) => (
              <StyledLogoWrapper key={i}>
                <Image src={src} alt={`logo-${i}`} width={100} height={70} />
              </StyledLogoWrapper>
            ))}
          </StyledTrack>
        </StyledMarquee>
      </StyledRoot>
    </AppPageSection>
  );
};

export default CustomerLogos;
