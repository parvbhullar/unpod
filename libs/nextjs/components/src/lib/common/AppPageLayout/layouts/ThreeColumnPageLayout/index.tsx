import type { HTMLAttributes, ReactNode } from 'react';

import {
  type LayoutType,
  StyledMainContainer,
  StyledPageRoot,
} from './index.styled';

type ThreeColumnPageLayoutProps = HTMLAttributes<HTMLDivElement> & {
  sidebar?: ReactNode;
  children?: ReactNode;
  rightSidebar?: ReactNode;
  layoutType?: LayoutType;};

const ThreeColumnPageLayout = ({
  sidebar,
  children,
  rightSidebar,
  layoutType = 'three-columns',
  ...restProps
}: ThreeColumnPageLayoutProps) => {
  return (
    <StyledPageRoot $layoutType={layoutType} {...restProps}>
      {sidebar}
      <StyledMainContainer>{children}</StyledMainContainer>
      {rightSidebar}
    </StyledPageRoot>
  );
};

export default ThreeColumnPageLayout;
