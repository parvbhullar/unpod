import React from 'react';
import { Col, Row } from 'antd';
import AppPageSection from '@unpod/components/common/AppPageSection';
import {
  StyledBadge,
  StyledButton,
  StyledCenterTime,
  StyledChartColumn,
  StyledChartWrapper,
  StyledDividerLine,
  StyledDot,
  StyledHeading,
  StyledIconCircle,
  StyledLabel,
  StyledLabelLeft,
  StyledLabelRight,
  StyledLine,
  StyledParagraph,
  StyledStatBox,
  StyledStatsWrapper,
  StyledSubText,
} from './index.styled';

import { CheckOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useIntl } from 'react-intl';

const LightningIntegration = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection
      style={{ padding: '80px 0', backgroundColor: '#12192b' }}
      id="lightning-integration"
      headerMaxWidth={1280}
    >
      <Row gutter={[0, 0]} align="middle">
        <Col xs={24} md={12}>
          <StyledBadge>
            {formatMessage({ id: 'sipLightning.badge' })}
          </StyledBadge>
          <StyledHeading level={2}>
            {formatMessage({ id: 'sipLightning.heading' })}
          </StyledHeading>
          <StyledParagraph>
            {formatMessage({ id: 'sipLightning.description' })}
          </StyledParagraph>
          <StyledButton type="primary" href="/bridges">
            {formatMessage({ id: 'sipLightning.cta' })}
          </StyledButton>
        </Col>

        <Col xs={24} md={12}>
          <StyledChartWrapper>
            <div className="chart-column">
              <StyledChartColumn>
                <StyledDot $top="20px" $color="#f44336" />
                <StyledLine $color="#cb4154" $height="430px" />
                <StyledIconCircle
                  $top="400px"
                  $border="#f44336"
                  $fill="#f44336"
                >
                  <ClockCircleOutlined style={{ color: 'white' }} />
                </StyledIconCircle>
                <StyledLabel $top="400px" $color="#f44336">
                  {formatMessage({ id: 'sipLightning.stillWorking' })}
                </StyledLabel>
                <StyledSubText $top="425px">
                  {formatMessage({ id: 'sipLightning.stillTime' })}
                </StyledSubText>
                <StyledLabelLeft $top="0px" $color="#f44336">
                  {formatMessage({ id: 'sipLightning.others' })}
                </StyledLabelLeft>
              </StyledChartColumn>
            </div>

            <div className="chart-column">
              <StyledChartColumn>
                <StyledDot $top="20px" $color="#00d25b" />
                <StyledLine $color="#00d25b" />
                <StyledIconCircle $top="70px" $fill="#00d25b" $border="#00d25b">
                  <CheckOutlined style={{ color: '#000' }} />
                </StyledIconCircle>
                <StyledLabel
                  $top="70px"
                  $left="calc(50% + 30px)"
                  $color="#00d25b"
                >
                  {formatMessage({ id: 'sipLightning.complete' })}
                </StyledLabel>
                <StyledSubText $top="85px" $left="calc(50% + 30px)">
                  {formatMessage({ id: 'sipLightning.fastTime' })}
                </StyledSubText>
                <StyledLabelRight $top="0px" $color="#00d25b">
                  {formatMessage({ id: 'sipLightning.unpod' })}
                </StyledLabelRight>
              </StyledChartColumn>
            </div>

            <StyledCenterTime>
              <div className="icon">
                <ClockCircleOutlined />
              </div>
              <div className="label">
                {formatMessage({ id: 'sipLightning.centerLabel' })}
              </div>
            </StyledCenterTime>
          </StyledChartWrapper>
        </Col>
      </Row>

      <StyledDividerLine />

      <StyledStatsWrapper>
        <StyledStatBox>
          <div className="value">
            {formatMessage({ id: 'sipLightningStats.value1' })}s
          </div>
          <div className="label">
            {formatMessage({ id: 'sipLightningStats.label1' })}
          </div>
        </StyledStatBox>
        <StyledStatBox>
          <div className="value">99.9%</div>
          <div className="label">
            {formatMessage({ id: 'sipLightningStats.label2' })}
          </div>
        </StyledStatBox>
        <StyledStatBox>
          <div className="value">24/7</div>
          <div className="label">
            {formatMessage({ id: 'sipLightningStats.label3' })}
          </div>
        </StyledStatBox>
      </StyledStatsWrapper>
    </AppPageSection>
  );
};

export default LightningIntegration;
