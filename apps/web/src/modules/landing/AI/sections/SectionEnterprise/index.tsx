import React from 'react';
import { Button } from 'antd';
import { useRouter } from 'next/navigation';
import { StyledContainer, StyledPageSection } from './index.styled';

const SectionEnterprise = () => {
  const router = useRouter();

  const onGetStarted = () => {
    router.push('/enterprise');
  };

  return (
    <StyledPageSection
      heading="Try for your enterprise team!"
      // bgColor="#0A0B20"
      bgColor="#15203A"
      // bgColor={lighten(0.05, '#796CFF')}
    >
      <StyledContainer>
        <Button
          type="primary"
          shape="round"
          size="large"
          onClick={onGetStarted}
        >
          Get Started
        </Button>
      </StyledContainer>
    </StyledPageSection>
  );
};

export default SectionEnterprise;
