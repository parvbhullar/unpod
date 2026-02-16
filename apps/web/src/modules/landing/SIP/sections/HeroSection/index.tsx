import {
  ArrowRightOutlined,
  CheckCircleTwoTone,
  CodeOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  StyledButtonRow,
  StyledCenterSection,
  StyledFeatureRow,
  StyledFeatureTag,
  StyledHeadline,
  StyledHighlight,
  StyledPillTag,
  StyledPrimaryButton,
  StyledSecondaryButton,
  StyledSubtitle,
} from './index.styled';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { useAuthContext } from '@unpod/providers';
import { GrDocumentText } from 'react-icons/gr';
import React from 'react';
import { useIntl } from 'react-intl';

export const HeroSection = () => {
  const { isAuthenticated } = useAuthContext();
  const { formatMessage } = useIntl();

  return (
    <AppPageSection
      style={{
        background: `radial-gradient(circle at 35% 40%, rgba(55,125,255,0.3) 0%, transparent 20%),
                  radial-gradient(circle at 65% 60%, rgba(168,57,255,0.3) 0%, transparent 20%)`,
      }}
    >
      <StyledCenterSection>
        <StyledPillTag>
          <ThunderboltOutlined style={{ color: '#377dff', fontSize: 18 }} />
          {formatMessage({ id: 'sipSectionHeader.pill' })}
        </StyledPillTag>

        <StyledHeadline level={1}>
          <StyledHighlight>
            {formatMessage({ id: 'sipSectionHeader.headingActive' })}{' '}
          </StyledHighlight>
          {formatMessage({ id: 'sipSectionHeader.heading' })}
        </StyledHeadline>

        <StyledSubtitle>
          {formatMessage({ id: 'sipSectionHeader.subTitle' })}
        </StyledSubtitle>

        <StyledButtonRow>
          <StyledPrimaryButton
            type="primary"
            size="large"
            href={isAuthenticated ? '/bridges' : '/contact-us'}
          >
            {formatMessage({
              id: isAuthenticated
                ? 'sipSectionHeader.primaryAuth'
                : 'sipSectionHeader.primaryGuest',
            })}
            <ArrowRightOutlined />
          </StyledPrimaryButton>

          <StyledSecondaryButton
            size="large"
            href="https://docs.unpod.dev/"
            target="_blank"
            rel="noopener noreferrer"
            icon={<GrDocumentText size={18} />}
          >
            {formatMessage({ id: 'sipSectionHeader.docs' })}
          </StyledSecondaryButton>

          {/*<StyledSecondaryButton size="large">
       Watch Demo <CaretRightOutlined/>
      </StyledSecondaryButton>*/}
        </StyledButtonRow>

        <StyledFeatureRow>
          <StyledFeatureTag>
            <CheckCircleTwoTone
              twoToneColor="#52c41a"
              style={{ fontSize: 16 }}
            />
            {formatMessage({ id: 'sipSectionHeader.feature1' })}
          </StyledFeatureTag>
          <StyledFeatureTag>
            <CodeOutlined style={{ color: '#377dff', fontSize: 16 }} />
            {formatMessage({ id: 'sipSectionHeader.feature2' })}
          </StyledFeatureTag>
          <StyledFeatureTag>
            <ThunderboltOutlined style={{ color: '#ffd666', fontSize: 16 }} />
            {formatMessage({ id: 'sipSectionHeader.feature3' })}
          </StyledFeatureTag>
        </StyledFeatureRow>
      </StyledCenterSection>
    </AppPageSection>
  );
};

export default HeroSection;
