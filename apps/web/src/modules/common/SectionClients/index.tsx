'use client';
import React from 'react';
import { useTheme } from 'styled-components';
import AppPageSection from '@unpod/components/common/AppPageSection';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledClientBox,
  StyledContainer,
  StyledListContainer,
} from './index.styled';
import type { SectionClientItem } from '@unpod/constants/types';

type SectionClientsProps = {
  heading?: string;
  items: SectionClientItem[];
};

const SectionClients: React.FC<SectionClientsProps> = ({ heading, items }) => {
  const theme = useTheme();

  return (
    <AppPageSection
      heading={heading}
      bgColor={theme.palette.common.white}
      headerMaxWidth={800}
      id="clients"
    >
      <StyledContainer>
        <StyledListContainer>
          {items
            .filter((item) => Boolean(item.logo))
            .map((item) => (
              <StyledClientBox key={item.id}>
                <AppImage
                  src={item.logo as string}
                  alt={item.name || 'Client Logo'}
                  layout="fixed"
                  width={150}
                  height={120}
                  style={{ margin: 10 }}
                />
              </StyledClientBox>
            ))}
        </StyledListContainer>
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionClients;
