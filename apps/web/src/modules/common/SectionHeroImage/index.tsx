import React from 'react';
import AppImage from '@unpod/components/next/AppImage';
import styled from 'styled-components';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { useMediaQuery } from 'react-responsive';
import { TabWidthQuery } from '@unpod/constants';

export const StyledContainer = styled.div`
  position: relative;
  aspect-ratio: 1170 / 438;
  width: 88%;
  margin: 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    aspect-ratio: 378 / 834;
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

const style = {
  background: 'url(/images/landing/how-it-works/howitworks-background.webp)',
  backgroundSize: 'cover',
  backgroundRepeat: 'repeat',
  backgroundPosition: 'center',
  padding: '30px 0 20px',
};

type SectionHeroImageProps = React.ComponentProps<typeof AppPageSection> & {
  children?: React.ReactNode;
};

const SectionHeroImage: React.FC<SectionHeroImageProps> = ({
  children,
  ...props
}) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  return (
    <AppPageSection style={style} {...props}>
      <StyledContainer>
        {children || (
          <AppImage
            src={
              isTabletOrMobile
                ? '/images/landing/connector-app-mobile.svg'
                : '/images/landing/connector-app.svg'
            }
            alt="Connector Apps"
            layout="fill"
            /*width={384}
            height={75}*/
          />
        )}
      </StyledContainer>
    </AppPageSection>
  );
};

export default SectionHeroImage;
