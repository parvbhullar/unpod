import React from 'react';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { Col, Row } from 'antd';
import {
  StyledLightningButton,
  StyledLightningDesc,
  StyledLightningHeadline,
  StyledLightningStat,
  StyledLightningStatsRow,
  StyledLightningTag,
  StyledLightningTimeline,
  StyledLightningTimelineDot,
  StyledLightningTimelineItem,
  StyledLightningTimelineLabel,
  StyledLightningTimelineWrap,
} from './index.styled';

const LightningIntegrationSection = () => (
  <AppPageSection
    style={{
      background: '#121826',
      padding: '72px 0 44px 0',
      color: '#fff',
    }}
    id="lightning-integration"
  >
    <Row
      gutter={[48, 32]}
      align="middle"
      justify="center"
      style={{ maxWidth: 1200, margin: '0 auto' }}
    >
      <Col
        xs={24}
        md={10}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-start',
        }}
      >
        <StyledLightningTag>⚡ Lightning fast integration</StyledLightningTag>
        <StyledLightningHeadline>
          Integration in under 1 hour
        </StyledLightningHeadline>
        <StyledLightningDesc>
          While our competitors can take days or weeks to get you up and
          running, VoiceBridge gets you integrated and making calls in under 1
          hour. We’ve streamlined the entire process with our developer-first
          API and comprehensive SDKs, making integration incredibly simple for
          everyone.
        </StyledLightningDesc>
        <StyledLightningButton type="primary" size="middle">
          Get Started
        </StyledLightningButton>
      </Col>
      <Col
        xs={24}
        md={14}
        style={{
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'center',
        }}
      >
        <StyledLightningTimelineWrap>
          <StyledLightningTimeline>
            {/* Competitor Timeline */}
            <StyledLightningTimelineItem $competitor>
              <StyledLightningTimelineDot $competitor />
              <StyledLightningTimelineLabel
                $competitor
                style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}
              >
                Competitor
              </StyledLightningTimelineLabel>
              <div
                style={{
                  color: '#ff6b6b',
                  fontWeight: 500,
                  fontSize: 15,
                  marginTop: 18,
                  marginBottom: 2,
                  textAlign: 'center',
                }}
              >
                Still Working
              </div>
              <div
                style={{ color: '#b3b8c8', fontSize: 14, textAlign: 'center' }}
              >
                72 hours
                <br />
                +Days more...
              </div>
            </StyledLightningTimelineItem>

            {/* VoiceBridge Timeline */}
            <StyledLightningTimelineItem $voicebridge>
              <StyledLightningTimelineDot $voicebridge />
              <StyledLightningTimelineLabel
                $voicebridge
                style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}
              >
                VoiceBridge
              </StyledLightningTimelineLabel>
              <div
                style={{
                  color: '#ffe066',
                  fontWeight: 700,
                  fontSize: 15,
                  marginTop: 18,
                  marginBottom: 2,
                  textAlign: 'center',
                }}
              >
                Complete
              </div>
              <div
                style={{ color: '#ffe066', fontSize: 14, textAlign: 'center' }}
              >
                {'< 1 hour'}
              </div>
            </StyledLightningTimelineItem>
          </StyledLightningTimeline>
          <div
            style={{
              color: '#b3b8c8',
              fontSize: 14,
              textAlign: 'center',
              marginTop: 30,
            }}
          >
            Time to Integration
          </div>
        </StyledLightningTimelineWrap>
      </Col>
    </Row>
    <StyledLightningStatsRow>
      <StyledLightningStat>
        <div
          style={{
            color: '#ffe066',
            fontWeight: 700,
            fontSize: '1.3rem',
            marginBottom: 2,
          }}
        >
          {'< 1hr'}
        </div>
        <div style={{ color: '#b3b8c8', fontSize: '0.97rem' }}>
          Complete Integration
        </div>
      </StyledLightningStat>
      <StyledLightningStat>
        <div
          style={{
            color: '#4ADE80',
            fontWeight: 700,
            fontSize: '1.3rem',
            marginBottom: 2,
          }}
        >
          99.9%
        </div>
        <div style={{ color: '#b3b8c8', fontSize: '0.97rem' }}>
          Success Rate
        </div>
      </StyledLightningStat>
      <StyledLightningStat>
        <div
          style={{
            color: '#60a5fa',
            fontWeight: 700,
            fontSize: '1.3rem',
            marginBottom: 2,
          }}
        >
          24/7
        </div>
        <div style={{ color: '#b3b8c8', fontSize: '0.97rem' }}>
          Support Available
        </div>
      </StyledLightningStat>
    </StyledLightningStatsRow>
  </AppPageSection>
);

export default LightningIntegrationSection;
