import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledFeaturesContent,
  StyledFeaturesPanel,
  StyledFeaturesWrapper,
} from './index.styled';
import FeatureCard from './FeatureCard';
import AnchorLink from 'react-anchor-link-smooth-scroll';
import Scrollspy, { type ScrollSpyProps } from '@unpod/components/ScrollSpy';
import AppImage from '@unpod/components/next/AppImage';

type FeaturesContentItem = {
  menuId: string;
  image: string;
};

type FeaturesPanelItem = {
  id: string | number;
  image: string;
  title: string;
  description?: string;
};

type FeaturesData = {
  heading?: React.ReactNode;
  subHeading?: React.ReactNode;
  featuresContent?: FeaturesContentItem[];
  featuresPanel?: FeaturesPanelItem[];
};

type FeaturesProps = ScrollSpyProps & {
  className?: string;
  data: FeaturesData;
};

const Features: React.FC<FeaturesProps> = ({ className, data, ...rest }) => {
  const scrollItems: string[] = [];
  const featureContent = data?.featuresContent ?? [];
  const featuresPanel = data?.featuresPanel ?? [];

  // convert menu path to scrollspy items
  featureContent.forEach((item) => {
    scrollItems.push(`#${item.menuId}`.slice(1));
  });
  // Add all classs to an array
  const addAllClasses = ['scrollspy__menu'];

  // className prop checking
  if (className) {
    addAllClasses.push(className);
  }

  return (
    <AppPageSection
      heading={data.heading}
      subHeading={data.subHeading}
      headerMaxWidth={800}
      id="about-us"
    >
      <StyledFeaturesWrapper>
        <StyledFeaturesContent>
          <Scrollspy
            items={scrollItems}
            className={addAllClasses.join(' ')}
            drawerClose={() => {
              console.log('drawerClose');
            }}
            {...rest}
          >
            {featureContent.map((item, index) => (
              <li key={index}>
                <AnchorLink href={`#${item.menuId}`}>
                  <AppImage
                    src={item.image}
                    alt="security"
                    height={432}
                    width={776}
                    layout="responsive"
                  />
                  {/*{item.menuId}*/}
                </AnchorLink>
              </li>
            ))}
          </Scrollspy>
        </StyledFeaturesContent>

        <StyledFeaturesPanel>
          <Scrollspy
            items={scrollItems}
            className={addAllClasses.join(' ')}
            drawerClose={() => {
              console.log('drawerClose');
            }}
            {...rest}
          >
            {featuresPanel.map((item, index) => (
              <li key={index} id={'feature-' + item.id}>
                <FeatureCard data={item} />
              </li>
            ))}
          </Scrollspy>
        </StyledFeaturesPanel>
      </StyledFeaturesWrapper>
    </AppPageSection>
  );
};

export default React.memo(Features);
