'use client';
import {
  StyledButtonRow,
  StyledCenterSection,
  StyledHeading,
  StyledHighlight,
  StyledPrimaryButton,
  StyledSecondaryButton,
  StyledSubtitle,
} from './index.styled';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { useRouter } from 'next/navigation';
import { useIntl } from 'react-intl';

export const HeroSection = () => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  return (
    <AppPageSection
      style={{
        background: `radial-gradient(circle at 35% 40%, rgba(55,125,255,0.3) 0%, transparent 20%),
                  radial-gradient(circle at 65% 60%, rgba(168,57,255,0.3) 0%, transparent 20%)`,
      }}
    >
      <StyledCenterSection>
        {/* <StyledPillTag>
          <ThunderboltOutlined style={{ color: '#377dff', fontSize: 18 }} />
          Seamless SIP-Voice AI Integration
        </StyledPillTag> */}

        <StyledHeading level={1}>
          {formatMessage({ id: 'hero.heading' })}
          <StyledHighlight>
            {formatMessage({ id: 'hero.headingHighlight' })}
          </StyledHighlight>
        </StyledHeading>

        <StyledSubtitle>
          {formatMessage({ id: 'hero.subtitle' })}
        </StyledSubtitle>

        <StyledButtonRow>
          <StyledPrimaryButton
            type="primary"
            size="large"
            onClick={() => router.push('/new/onboarding/')}
          >
            {formatMessage({ id: 'hero.primaryCta' })}
          </StyledPrimaryButton>
          <StyledSecondaryButton
            type="default"
            size="large"
            href="https://docs.unpod.dev/"
            target="_blank"
            rel="noopener noreferrer"
          >
            {formatMessage({ id: 'common.documentation' })}
          </StyledSecondaryButton>
        </StyledButtonRow>
      </StyledCenterSection>
    </AppPageSection>
  );
};

export default HeroSection;
