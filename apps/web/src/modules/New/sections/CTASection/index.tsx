'use client';
import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledCard,
  StyledCardBody,
  StyledCardDescription,
  StyledCardTitle,
  StyledParagraph,
  StyledPrimaryButton,
} from './index.styled';
import { useIntl } from 'react-intl';

const style = {
  background: 'linear-gradient(120deg, #377dff 0%, #a259e6 100%)',
};

const CTASection = () => {
  const { formatMessage } = useIntl();

  return (
    <AppPageSection style={style}>
      <StyledCard>
        <StyledCardBody>
          <StyledCardTitle>
            {formatMessage({ id: 'aiCta.title' })}
          </StyledCardTitle>

          <StyledCardDescription>
            {formatMessage({ id: 'aiCta.description' })}
          </StyledCardDescription>

          <StyledPrimaryButton type="primary" size="large" href="/contact-us/">
            {formatMessage({ id: 'aiCta.button' })}
          </StyledPrimaryButton>

          <StyledParagraph>
            {formatMessage({ id: 'aiCta.note' })}
          </StyledParagraph>
        </StyledCardBody>
      </StyledCard>
    </AppPageSection>
  );
};

export default CTASection;
