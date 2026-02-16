import React from 'react';
import FeatureCard from './FeatureCard';
import {
  StyledContainer,
  StyledListContainer,
  StyledPageSection,
} from './index.styled';
import type {
  SectionHeadingProps,
  SectionListItem,
} from '@unpod/constants/types';

type SectionUseCasesProps = SectionHeadingProps & {
  items: SectionListItem[];
  tabs?: Array<{
    id: string | number;
    title: string;
    items: SectionListItem[];
  }>;
};

const SectionUseCases: React.FC<SectionUseCasesProps> = ({
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

        {/*<StyledTabs
          defaultActiveKey="1"
          items={tabs.map((item) => ({
            key: item.id,
            label: item.title,
            children: (
              <StyledListContainer>
                {item.items.map((item) => (
                  <FeatureCard key={item.id} data={item} />
                ))}
              </StyledListContainer>
            ),
          }))}
        />*/}
      </StyledContainer>
    </StyledPageSection>
  );
};

export default SectionUseCases;
