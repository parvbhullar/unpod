import type { CSSProperties, ReactNode } from 'react';

import { StyledContainer, StyledSection } from './index.styled';
import AppSectionHeader from './AppSectionHeader';

type AppPageSectionProps = {
  children?: ReactNode;
  bgColor?: string;
  style?: CSSProperties;
  id?: string;
  heading?: ReactNode;
  subHeading?: ReactNode;
  description?: ReactNode;
  headerMaxWidth?: number;
  extra?: ReactNode;};

const AppPageSection = ({
  children,
  bgColor = 'transparent',
  style,
  id,
  ...restProps
}: AppPageSectionProps) => {
  return (
    <StyledSection $bgColor={bgColor} style={style} id={id}>
      <StyledContainer>
        <AppSectionHeader {...restProps} />
        {children}
      </StyledContainer>
    </StyledSection>
  );
};

export default AppPageSection;
