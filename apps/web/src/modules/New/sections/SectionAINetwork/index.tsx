'use client';
import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { AiOutlineApartment } from 'react-icons/ai';
import {
  StyledCard,
  StyledCardIcon,
  StyledGrid,
  StyledSubTitle,
  StyledTitle,
} from './index.styled';
import { RiBrain2Line } from 'react-icons/ri';
import { HiOutlineUsers } from 'react-icons/hi';
import { Card } from 'antd';
import { useIntl } from 'react-intl';

const { Meta } = Card;

const spaces = [
  {
    label: 'aiNetwork.identityHubTitle',
    description: 'aiNetwork.identityHubDescription',
    icon: <AiOutlineApartment size={40} />,
  },
  {
    label: 'aiNetwork.routingTitle',
    description: 'aiNetwork.routingDescription',
    icon: <RiBrain2Line size={40} />,
  },
  {
    label: 'aiNetwork.ecosystemTitle',
    description: 'aiNetwork.ecosystem.description',
    icon: <HiOutlineUsers size={40} />,
  },
];

const SectionAINetwork = () => {
  const { formatMessage } = useIntl();

  return (
    <AppPageSection
      style={{
        background:
          'radial-gradient(ellipse 60% 40% at 80% 30%, #e5d6ff 0%, #f8fafd 60%, #f6e5fa 100%)',
        // padding: '64px 0 64px 0',
      }}
    >
      <StyledTitle>{formatMessage({ id: 'aiNetwork.title' })}</StyledTitle>
      <StyledSubTitle>
        {formatMessage({ id: 'aiNetwork.subTitle' })}
      </StyledSubTitle>

      <StyledGrid>
        {spaces.map((space, index) => (
          <StyledCard key={index}>
            <StyledCardIcon>{space.icon}</StyledCardIcon>
            <Meta
              title={formatMessage({ id: space.label })}
              description={formatMessage({ id: space.description })}
            />
          </StyledCard>
        ))}
      </StyledGrid>
    </AppPageSection>
  );
};

export default SectionAINetwork;
