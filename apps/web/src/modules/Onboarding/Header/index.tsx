import React from 'react';
import { StyledHeader, StyledLogo } from './index.styled';
import AppImage from '@unpod/components/next/AppImage';
import { Flex } from 'antd';
import StepHeader from '@/modules/Onboarding/steps/StepHeader';
import AppLink from '@unpod/components/next/AppLink';

const Header = () => {
  return (
    <StyledHeader>
      <Flex align="center" justify="center">
        <StyledLogo>
          <AppLink href="/ai-studio">
            <AppImage
              src="/images/unpod/logo.svg"
              alt="unpod logo"
              height={32}
              width={120}
            />
          </AppLink>
        </StyledLogo>
        <StepHeader />
      </Flex>
    </StyledHeader>
  );
};

export default Header;
