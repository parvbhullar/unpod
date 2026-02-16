import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { Col, Row, Typography } from 'antd';
import {
  ApiOutlined,
  CheckCircleTwoTone,
  CustomerServiceOutlined,
  GlobalOutlined,
  SafetyOutlined,
} from '@ant-design/icons';
import {
  StyledCardIcon,
  StyledCardPill,
  StyledCardPills,
  StyledCardTitle,
  StyledCardWrapper,
  StyledChecklist,
  StyledDevCard,
  StyledPillTag,
  StyledStatCard,
  StyledStatLabel,
  StyledStatRow,
  StyledStatValue,
} from './index.styled';
import AppGrid from '@unpod/components/common/AppGrid';
import { useIntl } from 'react-intl';

const { Title, Text } = Typography;

const cardData = [
  {
    icon: <ApiOutlined />,
    title: 'sipInnovation.card1.title',
    highlight: '#3b82f6',
    pills: ['SIP 2.0', 'WebRTC', 'RTP/SRTP', 'STUN/TURN'],
  },
  {
    icon: <CustomerServiceOutlined />,
    title: 'sipInnovation.card2.title',
    highlight: '#a856f7',
    pills: ['G.711 (PCMU/PCMA)', 'G.722', 'Opus', 'G.729'],
  },
  {
    icon: <GlobalOutlined />,
    title: 'sipInnovation.card3.title',
    highlight: '#38d996',
    pills: ['Multi-Region Edges', 'Low Latency'],
  },
  {
    icon: <SafetyOutlined />,
    title: 'sipInnovation.card4.title',
    highlight: '#ef4443',
    pills: ['TLS 1.3', 'SRTP', 'OAuth 2.0', 'HIPAA Ready'],
  },
];

const stats = [
  {
    value: '5min',
    label: 'sipInnovation.setupTime',
    color: '#377dff',
    bg: '#f0f6ff',
  },
  {
    value: '99.9%',
    label: 'sipInnovation.upTime',
    color: '#9254de',
    bg: '#f7f0ff',
  },
];

export const InnovationSection = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection
      headerMaxWidth={1280}
      style={{
        background:
          'radial-gradient(ellipse 60% 40% at 80% 30%, #e5d6ff 0%, #f8fafd 60%, #f6e5fa 100%)',
        padding: '64px 0 64px 0',
      }}
      id="innovation"
    >
      <Row
        gutter={[{ xs: 0, sm: 0, md: 48, lg: 48 }, 32]}
        align="middle"
        justify="center"
        style={{ marginBottom: '5%' }}
      >
        <Col
          xs={24}
          md={12}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
          }}
        >
          <StyledPillTag>
            {formatMessage({ id: 'sipInnovation.pill' })}
          </StyledPillTag>
          <Title
            level={2}
            style={{
              fontWeight: 800,
              color: '#181c32',
              fontSize: '2.1rem',
              lineHeight: 1.18,
              marginBottom: 0,
            }}
          >
            {formatMessage({ id: 'sipInnovation.heading.line1' })}
            <br />
            <span style={{ color: '#7d5fff' }}>
              {formatMessage({ id: 'sipInnovation.heading.line2' })}
            </span>
          </Title>
          <Text
            style={{
              color: '#464d61',
              fontSize: '1.08rem',
              margin: '22px 0 0 0',
              fontWeight: 400,
              letterSpacing: 0.1,
            }}
          >
            {formatMessage({ id: 'sipInnovation.description' })}
          </Text>
          <StyledChecklist>
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <li key={i}>
                <CheckCircleTwoTone twoToneColor="#52c41a" />
                {formatMessage({ id: `sipInnovation.check${i}` })}
              </li>
            ))}
          </StyledChecklist>
        </Col>
        <Col
          xs={24}
          md={12}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <StyledCardWrapper>
            {/*<StyledCodeCard>*/}
            {/*  <StyledCodeHeader>*/}
            {/*    <StyledCodeDot color="#ff5f56" />*/}
            {/*    <StyledCodeDot color="#ffbd2e" />*/}
            {/*    <StyledCodeDot color="#27c93f" />*/}
            {/*  </StyledCodeHeader>*/}
            {/*  /!*<StyledCodeBlock as="pre">*/}
            {/*    {codeLines.map((line, item) => (*/}
            {/*      <StyledCodeLine key={item} style={{ color: line.color }}>*/}
            {/*        {line.code}*/}
            {/*      </StyledCodeLine>*/}
            {/*    ))}*/}
            {/*  </StyledCodeBlock>*!/*/}
            {/*</StyledCodeCard>*/}
            <StyledStatRow>
              {stats.map(({ value, label, color, bg }) => (
                <StyledStatCard $bg={bg} key={label}>
                  <StyledStatValue $color={color}>{value}</StyledStatValue>
                  <StyledStatLabel $color={color}>
                    {formatMessage({ id: label })}
                  </StyledStatLabel>
                </StyledStatCard>
              ))}
            </StyledStatRow>
          </StyledCardWrapper>
        </Col>
      </Row>
      <AppGrid
        data={cardData}
        itemPadding={24}
        responsive={{
          xs: 1,
          sm: 1,
          md: 4,
          lg: 4,
          xl: 4,
        }}
        renderItem={(card) => (
          <StyledDevCard key={card.title} $highlight={card.highlight}>
            <StyledCardIcon $color={card.highlight}>{card.icon}</StyledCardIcon>
            <StyledCardTitle>
              {formatMessage({ id: card.title })}
            </StyledCardTitle>
            <StyledCardPills>
              {card.pills.map((pill) => (
                <StyledCardPill key={pill}>{pill}</StyledCardPill>
              ))}
            </StyledCardPills>
          </StyledDevCard>
        )}
      />
    </AppPageSection>
  );
};

export default InnovationSection;
