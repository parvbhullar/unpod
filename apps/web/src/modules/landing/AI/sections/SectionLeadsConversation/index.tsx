'use client';
import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  ColoredText,
  Container,
  ContentWrapper,
  Description,
  StyledHeadContainer,
  StyledImageContainer,
  StyledTitle,
} from './index.styled';
import { useMediaQuery } from 'react-responsive';
import AppImage from '@unpod/components/next/AppImage';
import { TabWidthQuery } from '@unpod/constants';

const style = {
  paddingBlock: '40px 20px',
};

const SectionLeadsConversation = () => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  return (
    <AppPageSection style={style}>
      <Container>
        <ContentWrapper>
          <StyledHeadContainer>
            <StyledTitle>
              Smart AI workspace that helps teams manage
              <ColoredText> communication like humans.</ColoredText>
            </StyledTitle>
            <Description>
              We bring an smart, empathetic AI to help teams to handle the
              communication like humans do with efficiency of softwares. It
              connects seamlessly with calls, whatsapp, email, CRM, and ERP
              systems. It communicates empathetically, understands context,
              takes actions, and keeps everything in one timeline.
            </Description>
          </StyledHeadContainer>
        </ContentWrapper>
        <StyledImageContainer>
          <AppImage
            src={
              isTabletOrMobile
                ? '/images/landing/banner-image-mobile.svg'
                : '/images/landing/banner-image.svg'
            }
            alt="Sharing graphic"
            layout="fill"
            objectFit="cover"
          />
        </StyledImageContainer>
      </Container>
    </AppPageSection>
  );
};

export default SectionLeadsConversation;
