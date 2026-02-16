import React from 'react';
import MetricsCard from './MetricsCard';
import { StyledContainer, StyledListContainer } from './index.styled';
import type { SectionMetricsItem } from '@unpod/constants/types';

const metrics: SectionMetricsItem[] = [
  {
    id: 1,
    icon: 'report',
    title: '20K+',
    description: 'landing.metricsTeportCurations',
  },
  {
    id: 2,
    icon: 'question',
    title: '90K+',
    description: 'landing.metricsQna',
  },
  {
    id: 3,
    icon: 'quality',
    title: '2000+',
    description: 'landing.metricsQualityChecks',
  },
];

const SectionMetrics = () => {
  return (
    <StyledContainer>
      <StyledListContainer>
        {metrics.map((item) => (
          <MetricsCard key={item.id} data={item} />
        ))}
      </StyledListContainer>
    </StyledContainer>
  );
};

export default SectionMetrics;
