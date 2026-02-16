import styled from 'styled-components';
import { Typography } from 'antd';

const { Title, Paragraph } = Typography;

export const StyledTitle = styled(Title)`
  && {
    color: #fff;
    font-size: 3.75rem;
    font-weight: 600 !important;
    text-align: center;
    margin-bottom: 24px;
    letter-spacing: -0.02em;
     @media (max-width: 768px) {
      font-size: 2rem;
  }
`;

export const StyledSubtitle = styled(Paragraph)`
  color: #ffffff;
  font-size: 1.25rem;
  margin: 0 auto 56px auto;
  line-height: 1.6;
  font-weight: 300;
  text-align: center;
  max-width: 1160px;
   @media (max-width: 768px) {
      font-size: 1rem;
`;

export const StyledFeatureCard = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 20px;
  min-height: 90px;
  text-align: left;
`;

export const StyledIconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  width: 48px;
  height: 48px;
  min-width: 48px;
  font-size: 22px;
  color: #fff;
`;

export const StyledFeatureTitle = styled(Title)`
  && {
    color: #ffffff;
    margin: 0 0 6px 0;
    font-size: 1.25rem;
    font-weight: 500 !important;
    text-align: left;
  }
`;

export const StyledFeatureDescription = styled(Paragraph)`
  && {
    color: #dbeafe;
    margin: 4px 0 0;
    font-size: 1rem;
    line-height: 1.5;
    text-align: left;
  }
`;
