'use client';
import AppImage from '@unpod/components/next/AppImage';
import {
  Container,
  ContentBox,
  ContentColumn,
  ImageColumn,
  SectionDescription,
  SectionTitle,
  SectionWrapper,
  StyledSubTitle,
  Title,
  VerticalLine,
} from './index.styled';
import { howItWorksData } from './howItWorksData';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { useIntl } from 'react-intl';

const style = {
  background: 'url(/images/landing/how-it-works/howitworks-background.webp)',
  backgroundSize: 'cover',
  backgroundRepeat: 'repeat',
  backgroundPosition: 'center',
  padding: '20px 0',
};

const SectionHowItWorks = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection style={style}>
      <Container>
        <Title>
          {formatMessage({ id: 'aiHowItWorks.sectionHeading' })}{' '}
          <span>
            {formatMessage({ id: 'aiHowItWorks.sectionHeadingActive' })}
          </span>
        </Title>
        <StyledSubTitle>
          {formatMessage({ id: 'aiHowItWorks.sectionSubTitle' })}
        </StyledSubTitle>

        <div style={{ position: 'relative' }}>
          <VerticalLine />

          {howItWorksData.map((section, index) => (
            <SectionWrapper key={index} $reverse={section.reverse}>
              <ContentColumn>
                <ContentBox $reverse={section.reverse}>
                  <SectionTitle level={2}>
                    {formatMessage({ id: section.title })}
                  </SectionTitle>
                  <SectionDescription>
                    {formatMessage({ id: section.description })}
                  </SectionDescription>
                </ContentBox>
              </ContentColumn>

              <ImageColumn>
                <AppImage
                  src={section.image}
                  alt={section.title}
                  width={465}
                  height={365}
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              </ImageColumn>
            </SectionWrapper>
          ))}
        </div>
      </Container>
    </AppPageSection>
  );
};

export default SectionHowItWorks;
