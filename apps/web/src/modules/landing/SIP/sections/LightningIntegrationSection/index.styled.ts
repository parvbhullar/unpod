import styled from 'styled-components';
import { Button, Steps } from 'antd';

export const StyledLightningTag = styled.div`
  display: inline-block;
  background: #23293a;
  color: #ffe066;
  font-size: 13px;
  font-weight: 600;
  border-radius: 20px;
  padding: 4px 16px;
  margin-bottom: 22px;
  letter-spacing: 0.02em;
`;

export const StyledLightningHeadline = styled.h2`
  color: #fff;
  font-size: 2.1rem;
  font-weight: 800;
  line-height: 1.15;
  margin-bottom: 0;
`;

export const StyledLightningDesc = styled.p`
  color: #b3b8c8;
  font-size: 1.03rem;
  font-weight: 400;
  margin: 24px 0 0 0;
  line-height: 1.7;
`;

export const StyledLightningButton = styled(Button)`
  margin-top: 28px;
  font-weight: 700;
  border-radius: 999px;
  background: linear-gradient(90deg, #ffe066 0%, #ffb800 100%);
  border: none;
  color: #181c32;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.07);
  &:hover {
    background: linear-gradient(90deg, #ffb800 0%, #ffe066 100%);
    color: #181c32;
  }
`;

export const StyledLightningTimelineWrap = styled.div`
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding-top: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const StyledLightningTimeline = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: flex-start;
  gap: 180px;
  width: 100%;
  position: relative;
  margin-bottom: 10px;
`;

export const StyledLightningTimelineItem = styled.div<{
  $competitor?: boolean;
  $voicebridge?: boolean;
}>`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 160px;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 50%;
    top: 22px;
    width: 2px;
    height: 90px;
    background: ${({ $competitor, $voicebridge }) =>
      $competitor
        ? 'linear-gradient(to bottom, #ff6b6b 0%, #23293a 100%)'
        : $voicebridge
          ? 'linear-gradient(to bottom, #ffe066 0%, #23293a 100%)'
          : '#b3b8c8'};
    transform: translateX(-50%);
    z-index: 1;
  }
`;

export const StyledLightningTimelineDot = styled.div<{
  $competitor?: boolean;
  $voicebridge?: boolean;
}>`
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: ${({ $competitor, $voicebridge }) =>
    $competitor ? '#ff6b6b' : $voicebridge ? '#ffe066' : '#b3b8c8'};
  border: 3px solid #23293a;
  margin-bottom: 7px;
  z-index: 2;
`;

export const StyledLightningTimelineLabel = styled.div<{
  $competitor?: boolean;
  $voicebridge?: boolean;
}>`
  color: ${({ $competitor, $voicebridge }) =>
    $competitor ? '#ff6b6b' : $voicebridge ? '#ffe066' : '#b3b8c8'};
  font-size: 14px;
  font-weight: 700;
  margin-top: 6px;
`;

export const StyledLightningStatsRow = styled.div`
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 64px;
  margin: 56px auto 0 auto;
  max-width: 800px;
`;

export const StyledLightningStat = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  background: none;
`;

export const StyledLightningSteps = styled(Steps)`
  background: none;
  padding: 18px 0 0 0;
  .ant-steps-item {
    .ant-steps-item-title {
      color: #fff !important;
    }
    .ant-steps-item-description {
      color: #b3b8c8 !important;
    }
  }
  .ant-steps-item-process .ant-steps-item-icon {
    background: #ffe066 !important;
    border-color: #ffe066 !important;
  }
  .ant-steps-item-finish .ant-steps-item-icon {
    background: #ff6b6b !important;
    border-color: #ff6b6b !important;
  }
  .ant-steps-item-icon {
    background: #23293a !important;
    border-color: #23293a !important;
  }
  .ant-steps-item-tail::after {
    background: #23293a !important;
  }
`;
