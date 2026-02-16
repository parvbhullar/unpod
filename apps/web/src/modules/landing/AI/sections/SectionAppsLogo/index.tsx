import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledClientBox,
  StyledContainer,
  StyledListContainer,
} from './index.styled';

type LogoItem = {
  id: string | number;
  logo: string;
  name: string;
};

type SectionAppsLogoProps = {
  items: LogoItem[];
  [key: string]: unknown;
};

const SectionAppsLogo: React.FC<SectionAppsLogoProps> = ({
  items,
  ...props
}) => {
  return (
    <AppPageSection {...props}>
      <StyledContainer>
        <StyledListContainer>
          {items.map((item) => (
            <StyledClientBox key={item.id}>
              <AppImage
                src={item.logo}
                alt={item.name}
                layout="fill"
                objectFit={'contain'}
                // width={80}
                // height={80}
              />
            </StyledClientBox>
          ))}
        </StyledListContainer>
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionAppsLogo;
