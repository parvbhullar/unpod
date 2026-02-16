'use client';
import React from 'react';
import AppLink from '@unpod/components/next/AppLink';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledHeader,
  StyledHeaderContainer,
  StyledLogo,
} from './index.styled';
import { useIsDesktop } from '@unpod/custom-hooks';

const LayoutHeader = () => {
  const { isDesktopApp } = useIsDesktop();

  return (
    <StyledHeader>
      <StyledHeaderContainer>
        <StyledLogo>
          <AppLink href={isDesktopApp ? '#' : '/'}>
            <AppImage
              src="/images/unpod/logo.svg"
              alt="unpod logo"
              height={38}
              width={120}
            />
          </AppLink>
        </StyledLogo>
      </StyledHeaderContainer>
    </StyledHeader>
  );
};

export default LayoutHeader;
