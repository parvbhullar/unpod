import React, {ReactNode} from 'react';
import SliderLayout from './layouts/SliderLayout';
import FullWidthLayout from './layouts/FullWidthLayout';

const PAGE_LAYOUTS = {
  slider: SliderLayout,
  full: FullWidthLayout,
};

type AppPageLayoutProps = {
  children: ReactNode;
  layout?: 'slider' | 'full';
};

const AppPageLayout: React.FC<AppPageLayoutProps> = ({
                                                       layout = 'slider',
                                                       ...restProps
                                                     }) => {
  const PageLayout = PAGE_LAYOUTS[layout];

  return <PageLayout {...restProps} />;
};

export default AppPageLayout;
