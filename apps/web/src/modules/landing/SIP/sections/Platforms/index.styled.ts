import styled, { keyframes } from 'styled-components';
import { Typography } from 'antd';

const { Title, Text } = Typography;

export const Badge = styled.div`
  display: inline-flex;
  align-items: center;
  background: linear-gradient(90deg, #f0f4ff, #f8f0ff);
  color: #1e3a8a;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 6px 16px;
  border-radius: 999px;
  margin-bottom: 20px;
  border: 1px solid rgba(0, 81, 255, 0.1);
`;

export const GradientText = styled.span`
  background: linear-gradient(90deg, #4f46e5, #8b5cf6, #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
`;

export const MetricsWrapper = styled.div`
  margin-top: 64px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: white;
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  padding: 40px 20px;
  gap: 20px;

  @media (max-width: 992px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 576px) {
    grid-template-columns: 1fr;
    text-align: center;
  }
`;

export const MetricItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const MetricValue = styled.div`
  font-size: 2rem;
  font-weight: 800;
  margin-bottom: 8px;
`;

export const MetricLabel = styled.div`
  font-size: 1rem;
  font-weight: 600;
  color: #2f3339;
  margin-bottom: 4px;
`;

export const MetricSubLabel = styled.div`
  font-size: 0.9rem;
  color: #6b6f81;
`;

export const StyledCard = styled.div<{ $highlight?: string }>`
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(80, 80, 180, 0.08);
  padding: 24px;
  position: relative;
  border: 2px solid ${({ $highlight }) => $highlight || '#e8ebf1'};
  transition:
    box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1),
    transform 0.35s cubic-bezier(0.22, 1, 0.36, 1);
  display: flex;
  flex-direction: column;
  will-change: box-shadow, transform;

  &:hover {
    box-shadow: 0 12px 40px rgba(80, 80, 180, 0.22);
    transform: translateY(-8px) scale(1.015);
  }
`;

export const StyledHeaderRow = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 5%;
`;

export const StyledLogoAndTitle = styled.div`
  display: flex;
  align-items: center;
`;

export const StyledLogoWrapper = styled.div`
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: #222222;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;

  & .ant-image-img {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    object-fit: contain;
  }
`;

export const StyledNameSubtitleBlock = styled.div`
  display: flex;
  flex-direction: column;
`;

export const StyledPopularBadge = styled.span`
  font-size: 0.6rem;
  background: linear-gradient(90deg, #4285f4 0%, #a259fa 100%);
  color: #fff;
  height: 20px;
  width: 80px;
  border-radius: 16px;
  font-weight: 600;
  padding: 2px 13px;
  display: flex;
  align-items: center;
  margin-left: 8px;
`;

export const StyledDescription = styled.div`
  color: #2a354d;
  font-size: 0.8rem;
  margin-bottom: 20px;
  margin-top: 14px;
`;

export const StyledFeaturesList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0 0 18px 0;
`;

export const StyledFeature = styled.li`
  color: #212b36;
  font-size: 0.8rem;
  font-weight: 400;
  margin-bottom: 12px;
  display: flex;
  align-items: center;

  svg {
    color: #2fd964;
    margin-right: 8px;
    font-size: 1.13em;
  }
`;

export const StyledStatusRow = styled.div`
  border-top: 1px solid #f0f3fa;
  padding-top: 16px;
  display: flex;
  justify-content: space-between;
  color: #7d8597;
  font-size: 1rem;
  align-items: center;
`;

export const blink = keyframes`
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
`;

export const StyledReadyDot = styled.span<{ $bgColor?: string }>`
  display: inline-block;
  width: 0.5rem;
  height: 0.5rem;
  background: ${({ $bgColor }) => $bgColor || '#16A34A'};
  border-radius: 50%;
  margin-right: 7px;
  animation: ${blink} 2.2s infinite;
`;

export const StyledStatusText = styled.span<{ $color?: string }>`
  color: ${({ $color }) => $color || '#16A34A'};
  font-weight: 500;
  font-size: 0.8rem;
`;

export const StyledTitle = styled(Title).attrs({ level: 4 })`
  && {
    margin-bottom: 4px;
    color: #1d3d6b;
    font-weight: 700;
    font-size: 20px;
    line-height: 1.15;
  }
`;

export const StyledSubtitle = styled(Text)`
  && {
    color: #2067e3;
    font-weight: 400;
    font-size: 0.8rem;
    line-height: 1.1;
  }
`;

export const StyledStatusLabel = styled.span`
  color: #798098;
  font-weight: 400;
  font-size: 0.8rem;
`;
