'use client';
import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { MdAdd } from 'react-icons/md';
import { useTheme } from 'styled-components';
import { StyledCollapse, StyledContainer } from './index.styled';
import type {
  SectionFaqItem,
  SectionHeadingProps,
} from '@unpod/constants/types';

type SectionFaqsProps = SectionHeadingProps & {
  items: SectionFaqItem[];
};

const SectionFaqs: React.FC<SectionFaqsProps> = ({
  heading,
  subHeading,
  description,
  items,
}) => {
  const theme = useTheme();

  return (
    <AppPageSection
      heading={heading}
      subHeading={subHeading}
      description={description}
      bgColor={theme.palette.primaryHover}
      id="faqs"
    >
      <StyledContainer>
        <StyledCollapse
          expandIcon={({ isActive }) => (
            <MdAdd
              style={{
                transform: isActive ? 'rotate(45deg)' : 'rotate(0deg)',
                fontSize: 20,
              }}
            />
          )}
          expandIconPlacement="end"
          items={items.map((item) => ({
            key: item.id,
            label: item.question,
            children: item.answer,
          }))}
        />
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionFaqs;
