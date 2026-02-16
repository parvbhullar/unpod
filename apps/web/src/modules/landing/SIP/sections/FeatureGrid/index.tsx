import React from 'react';
import {
  AppstoreOutlined,
  BarChartOutlined,
  CodeOutlined,
  GlobalOutlined,
  LockOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import {
  StyledCardDesc,
  StyledCardTitle,
  StyledFeatureCard,
  StyledIconCircle,
  StyledParagraph,
  StyledTitle,
} from './index.styled';
import AppPageSection from '@unpod/components/common/AppPageSection';
import AppGrid from '@unpod/components/common/AppGrid';
import { BiBot } from 'react-icons/bi';

const features = [
  {
    icon: <BiBot />,
    iconBg: '#fff0f6',
    iconColor: '#FF85C0',
    title: 'Third Party Platform Support',
    desc: 'Native support for voice ai platforms such as LiveKit, Daily, ElevenLabs, Azure, AWS..',
  },
  {
    icon: <ThunderboltOutlined />,
    iconBg: '#f0ebff',
    iconColor: '#7D5FFF',
    title: 'Lightning Fast Setup',
    desc: 'Connect your telephony with voice ai platform instantly under 1hr.',
  },
  {
    icon: <LockOutlined />,
    iconBg: '#e6fcfa',
    iconColor: '#36CFC9',
    title: 'Enterprise Security',
    desc: 'End-to-end encryption, HIPAA compliance, and ISO-27001 certification for mission-critical applications.',
  },
  {
    icon: <CodeOutlined />,
    iconBg: '#f4ffed',
    iconColor: '#52C41A',
    title: 'Developer First',
    desc: 'Comprehensive SDKs for JavaScript, Python, and Go with extensive documentation and code examples.',
  },
  {
    icon: <GlobalOutlined />,
    iconBg: '#f9f0ff',
    iconColor: '#9254DE',
    title: 'Global Infrastructure',
    desc: 'Edge nodes in 50+ countries ensuring low latency and high availability for worldwide deployments.',
  },
  {
    icon: <RobotOutlined />,
    iconBg: '#fffbe6',
    iconColor: '#faad14',
    title: 'AI-Powered',
    desc: 'Built-in voice AI capabilities including speech recognition, synthesis, and real-time processing.',
  },
  {
    icon: <AppstoreOutlined />,
    iconBg: '#e6f7ff',
    iconColor: '#36a3f7',
    title: 'Scalable Architecture',
    desc: 'Auto-scaling infrastructure that handles everything from startup MVPs to enterprise-grade applications.',
  },
  {
    icon: <BarChartOutlined />,
    iconBg: '#e6fffb',
    iconColor: '#13c2c2',
    title: 'Real-time Analytics',
    desc: 'Comprehensive monitoring and analytics dashboard with call quality metrics and usage insights.',
  },
  {
    icon: <SafetyCertificateOutlined />,
    iconBg: '#f9f0ff',
    iconColor: '#B37FEB',
    title: 'Compliance Ready',
    desc: 'Pre-built compliance features for GDPR, CCPA, and industry-specific regulations.',
  },
];

const FeatureGrid = () => (
  <AppPageSection
    headerMaxWidth={1280}
    style={{ margin: 0, marginTop: 50, padding: 0 }}
    heading={<StyledTitle>Everything You Need to Build</StyledTitle>}
    subHeading={
      <StyledParagraph>
        Our comprehensive platform provides all the tools and infrastructure you
        need to connect traditional telecom with modern AI capabilities.
      </StyledParagraph>
    }
  >
    <AppGrid
      data={features}
      itemPadding={24}
      responsive={{
        xs: 1,
        sm: 1,
        md: 2,
        lg: 3,
        xl: 3,
      }}
      renderItem={(item) => (
        <StyledFeatureCard key={item.title}>
          <StyledIconCircle $bg={item.iconBg}>
            {React.cloneElement(item.icon, {
              style: { color: item.iconColor, fontSize: 22 },
            })}
          </StyledIconCircle>
          <StyledCardTitle>{item.title}</StyledCardTitle>
          <StyledCardDesc>{item.desc}</StyledCardDesc>
        </StyledFeatureCard>
      )}
    />
  </AppPageSection>
);

export default FeatureGrid;
