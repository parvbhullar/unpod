import {
  BarChartOutlined,
  CodeOutlined,
  CustomerServiceOutlined,
  GlobalOutlined,
  LockOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import AppGrid from '@unpod/components/common/AppGrid';
import AppPageSection from '@unpod/components/common/AppPageSection';
import React from 'react';
import {
  StyledFeatureCard,
  StyledFeatureDescription,
  StyledFeatureTitle,
  StyledIconWrapper,
  StyledSubtitle,
  StyledTitle,
} from './index.styled';
import { useIntl } from 'react-intl';

const features = [
  {
    icon: <ThunderboltOutlined />,
    iconColor: '#FFCA2C',
    title: 'sipVoiceBridge.feature1.title',
    description: 'sipVoiceBridge.feature1.desc',
  },
  {
    icon: <CodeOutlined />,
    iconColor: '#567DFE',
    title: 'sipVoiceBridge.feature2.title',
    description: 'sipVoiceBridge.feature2.desc',
  },
  {
    icon: <CustomerServiceOutlined />,
    iconColor: '#A56CFF',
    title: 'sipVoiceBridge.feature3.title',
    description: 'sipVoiceBridge.feature3.desc',
  },
  {
    icon: <GlobalOutlined />,
    iconColor: '#38C984',
    title: 'sipVoiceBridge.feature4.title',
    description: 'sipVoiceBridge.feature4.desc',
  },
  {
    icon: <LockOutlined />,
    iconColor: '#FF5C5C',
    title: 'sipVoiceBridge.feature5.title',
    description: 'sipVoiceBridge.feature5.desc',
  },
  {
    icon: <BarChartOutlined />,
    iconColor: '#FF962C',
    title: 'sipVoiceBridge.feature6.title',
    description: 'sipVoiceBridge.feature6.desc',
  },
];

export const VoiceBridge = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection
      headerMaxWidth={1280}
      style={{
        padding: '60px 0 80px 0',
        background:
          'radial-gradient(circle at 0% 0%, #131e38 0%, #1d3885 60%, #502087 100%)',
      }}
      id="why-voicebridge"
      heading={
        <StyledTitle>
          {formatMessage({ id: 'sipVoiceBridge.heading' })}
        </StyledTitle>
      }
      description={
        <StyledSubtitle>
          {formatMessage({ id: 'sipVoiceBridge.subHeading' })}
        </StyledSubtitle>
      }
    >
      <AppGrid
        data={features}
        itemPadding={24}
        responsive={{
          xs: 1,
          sm: 1,
          md: 2,
          lg: 2,
          xl: 2,
        }}
        renderItem={(item) => (
          <StyledFeatureCard>
            <StyledIconWrapper>
              {React.cloneElement(item.icon, {
                style: { color: item.iconColor },
              })}
            </StyledIconWrapper>
            <div>
              <StyledFeatureTitle level={4}>
                {formatMessage({ id: item.title })}
              </StyledFeatureTitle>
              <StyledFeatureDescription>
                {formatMessage({ id: item.description })}
              </StyledFeatureDescription>
            </div>
          </StyledFeatureCard>
        )}
      />
    </AppPageSection>
  );
};
export default VoiceBridge;
