'use client';
import React from 'react';
import {
  StyledContainer,
  StyledListContainer,
  StyledPageSection,
} from './index.styled';
import FeatureCard from './FeatureCard';
import type {
  SectionHeadingProps,
  SectionListItem,
} from '@unpod/constants/types';

type SectionFeaturesProps = SectionHeadingProps & {
  items: SectionListItem[];
};

const SectionFeatures: React.FC<SectionFeaturesProps> = ({
  heading,
  subHeading,
  items,
}) => {
  return (
    <StyledPageSection
      heading={heading}
      subHeading={subHeading}
      bgColor="#091717"
      id="features"
    >
      <StyledContainer>
        <StyledListContainer>
          {items.map((item) => (
            <FeatureCard key={item.id} data={item} />
          ))}
        </StyledListContainer>
      </StyledContainer>
    </StyledPageSection>
  );
};

export default SectionFeatures;
