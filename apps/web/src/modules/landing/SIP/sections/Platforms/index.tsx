import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { Typography } from 'antd';
import PlatformItem from './PlatformItem';
import AppGrid from '@unpod/components/common/AppGrid';
import {
  Badge,
  GradientText,
  MetricItem,
  MetricLabel,
  MetricSubLabel,
  MetricsWrapper,
  MetricValue,
} from './index.styled';
import { ThunderboltOutlined } from '@ant-design/icons';
import { metrics, platforms } from './data';
import { useIntl } from 'react-intl';

const { Title, Text } = Typography;

const Platforms = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection
      heading={
        <>
          <Badge>
            <ThunderboltOutlined style={{ color: '#0051ff', marginRight: 8 }} />
            {formatMessage({ id: 'sipPlatforms.badge' })}
          </Badge>
          <Title
            level={2}
            style={{
              fontWeight: 700,
              color: '#000000',
              textAlign: 'center',
              fontSize: 40,
              marginBottom: 10,
              lineHeight: '1.3',
            }}
          >
            {formatMessage({ id: 'sipPlatforms.heading' })} <br />
            <GradientText>
              {formatMessage({ id: 'sipPlatforms.headingActive' })}
            </GradientText>
          </Title>
        </>
      }
      subHeading={
        <Text
          style={{
            color: '#3b3f4a',
            fontSize: '1.1rem',
            fontWeight: 400,
            textAlign: 'center',
            display: 'block',
            lineHeight: '1.6',
            maxWidth: 840,
            margin: '0 auto 34px',
            fontFamily: "'Inter', sans-serif",
          }}
        >
          {formatMessage({ id: 'sipPlatforms.subHeading' })}
        </Text>
      }
      headerMaxWidth={1280}
      style={{
        padding: '64px 0 36px 0',
        background: 'linear-gradient(180deg, #f6f9ff 0%, #ffffff 100%)',
      }}
    >
      <AppGrid
        data={platforms}
        itemPadding={24}
        responsive={{
          xs: 1,
          sm: 1,
          md: 2,
          lg: 3,
          xl: 3,
        }}
        renderItem={(item) => <PlatformItem key={item.name} item={item} />}
      />

      <MetricsWrapper>
        {metrics.map((item, index) => (
          <MetricItem key={index}>
            <MetricValue style={{ color: item.color }}>
              {item.value}
            </MetricValue>
            <MetricLabel>{formatMessage({ id: item.label })}</MetricLabel>
            <MetricSubLabel>
              {formatMessage({ id: item.subLabel })}
            </MetricSubLabel>
          </MetricItem>
        ))}
      </MetricsWrapper>
    </AppPageSection>
  );
};

export default Platforms;
