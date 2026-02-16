import {
  ArrowRightOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  UsergroupAddOutlined,
} from '@ant-design/icons';
import AppPageSection from '@unpod/components/common/AppPageSection';
import { Col } from 'antd';
import {
  StyledCallActionButtonWrapper,
  StyledCallActionCTAButton,
  StyledCallActionHeading,
  StyledCallActionNote,
  StyledCallActionStatCard,
  StyledCallActionStatLabel,
  StyledCallActionStatNumber,
  StyledCallActionStatRow,
  StyledCallActionSubtitle,
} from './index.styled';
import { useIntl } from 'react-intl';

export const CallAction = () => {
  const { formatMessage } = useIntl();
  return (
    <AppPageSection
      style={{
        minHeight: 420,
        background: 'linear-gradient(120deg, #377dff 0%, #a259e6 100%)',
      }}
      heading={
        <StyledCallActionHeading>
          {formatMessage({ id: 'sipCallAction.heading' })}
          <br />

          {formatMessage({ id: 'sipCallAction.headingActive' })}
        </StyledCallActionHeading>
      }
      subHeading={
        <StyledCallActionSubtitle>
          {formatMessage({ id: 'sipCallAction.subtitle' })}
        </StyledCallActionSubtitle>
      }
      headerMaxWidth={1280}
    >
      <StyledCallActionStatRow gutter={[32, 24]} justify="center">
        <Col xs={24} sm={12} md={8}>
          <StyledCallActionStatCard variant="borderless">
            <ClockCircleOutlined
              style={{ fontSize: 32, color: '#FFD666', marginBottom: 6 }}
            />
            <StyledCallActionStatNumber>5 min</StyledCallActionStatNumber>
            <StyledCallActionStatLabel>
              {formatMessage({ id: 'sipCallAction.stat1' })}
            </StyledCallActionStatLabel>
          </StyledCallActionStatCard>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <StyledCallActionStatCard variant="borderless">
            <UsergroupAddOutlined
              style={{ fontSize: 32, color: '#95de64', marginBottom: 6 }}
            />
            <StyledCallActionStatNumber>50+</StyledCallActionStatNumber>
            <StyledCallActionStatLabel>
              {formatMessage({ id: 'sipCallAction.stat2' })}
            </StyledCallActionStatLabel>
          </StyledCallActionStatCard>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <StyledCallActionStatCard variant="borderless">
            <ThunderboltOutlined
              style={{ fontSize: 32, color: '#fffbe6', marginBottom: 6 }}
            />
            <StyledCallActionStatNumber>99.9%</StyledCallActionStatNumber>
            <StyledCallActionStatLabel>
              {formatMessage({ id: 'sipCallAction.stat3' })}
            </StyledCallActionStatLabel>
          </StyledCallActionStatCard>
        </Col>
      </StyledCallActionStatRow>

      <StyledCallActionButtonWrapper>
        <StyledCallActionCTAButton type="primary" size="large" href="/bridges">
          {formatMessage({ id: 'sipCallAction.startBuilding' })}{' '}
          <ArrowRightOutlined />
        </StyledCallActionCTAButton>
      </StyledCallActionButtonWrapper>

      <StyledCallActionNote>
        {formatMessage({ id: 'sipCallAction.note' })}
      </StyledCallActionNote>
    </AppPageSection>
  );
};

export default CallAction;
