'use client';
import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledCard,
  StyledCardBody,
  StyledCardDescription,
  StyledCardIcon,
  StyledNumber,
  StyledPrimaryButton,
  StyledSubTitle,
  StyledTitle,
} from './index.styled';
import { IoCallOutline } from 'react-icons/io5';
import { useIntl } from 'react-intl';

const style = {
  background:
    'radial-gradient(circle at 0% 0%, #131e38 0%, #1d3885 60%, #502087 100%)',
};

const AiShowcase = () => {
  const { formatMessage } = useIntl();

  return (
    <AppPageSection style={style}>
      <StyledTitle>{formatMessage({ id: 'aiShowcase.title' })}</StyledTitle>
      <StyledSubTitle>
        {formatMessage({ id: 'aiShowcase.subTitle' })}
      </StyledSubTitle>

      <StyledCard>
        <StyledCardBody>
          <StyledCardDescription>
            {formatMessage({ id: 'aiShowcase.description' })}
          </StyledCardDescription>
          <StyledNumber>
            {' '}
            <StyledCardIcon>{<IoCallOutline size={44} />}</StyledCardIcon>+1
            (555) 123-AI-ID
          </StyledNumber>
          <StyledPrimaryButton type="primary" size="middle">
            <IoCallOutline size={22} />
            {formatMessage({ id: 'aiShowcase.callButton' })}
          </StyledPrimaryButton>
        </StyledCardBody>
      </StyledCard>
    </AppPageSection>
  );
};

export default AiShowcase;
