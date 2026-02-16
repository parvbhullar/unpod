import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import ServiceCard from './ServiceCard';
import { StyledContainer, StyledListContainer } from './index.styled';
import type {
  SectionHeadingProps,
  SectionListItem,
} from '@unpod/constants/types';

type SectionServicesProps = SectionHeadingProps & {
  items: SectionListItem[];
};

const SectionServices: React.FC<SectionServicesProps> = ({
  heading,
  subHeading,
  items,
}) => {
  return (
    <AppPageSection heading={heading} subHeading={subHeading} id="services">
      <StyledContainer>
        <StyledListContainer>
          {items.map((item) => (
            <ServiceCard key={item.id} data={item} />
          ))}
        </StyledListContainer>
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionServices;
