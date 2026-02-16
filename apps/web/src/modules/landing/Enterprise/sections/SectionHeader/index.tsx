'use client';
import React from 'react';

import { Button } from 'antd';
import { useRouter } from 'next/navigation';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { useAuthContext } from '@unpod/providers';
import SectionMetrics from '../../../../common/SectionMetrics';
import { StyledActionsContainer, StyledTitle } from './index.styled';
import { useIntl } from 'react-intl';

const SectionHeader = () => {
  const { isAuthenticated, user } = useAuthContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onGetStarted = () => {
    if (isAuthenticated) {
      router.push(`${user?.organization?.domain_handle}/org`);
    } else {
      router.push('/auth/signin');
    }
  };

  return (
    <AppPageSection
      heading={
        <StyledTitle>
          {formatMessage({ id: 'landing.headerTitle' })}
        </StyledTitle>
      }
      headerMaxWidth={830}
      subHeading={formatMessage({ id: 'landing.headerSubTitle' })}
    >
      <StyledActionsContainer>
        <Button type="primary" size="large" onClick={onGetStarted}>
          {formatMessage({ id: 'common.getStarted' })}
        </Button>
      </StyledActionsContainer>

      <SectionMetrics />
    </AppPageSection>
  );
};

export default SectionHeader;
