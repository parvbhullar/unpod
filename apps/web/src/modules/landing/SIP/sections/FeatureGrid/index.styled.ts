import styled from 'styled-components';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

export const StyledTitle = styled(Title)`
  font-size: 2.8rem !important;
  text-align: center;
  font-weight: 700 !important;
  margin-bottom: 8px !important;
  @media (max-width: 700px) {
    font-size: 2rem !important;
  }
`;

export const StyledParagraph = styled(Paragraph)`
  font-size: 1.2rem !important;
  text-align: center;
  margin: 0 auto 30px;
  font-size: 1.2rem;
  color: #6b6f81;
  @media (max-width: 700px) {
    font-size: 1.02rem !important;
  }
`;

export const StyledGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  max-width: 100%;
  margin: 40px auto 0 auto;
  width: 100%;
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
  @media (max-width: 700px) {
    grid-template-columns: 1fr;
    gap: 20px;
  }
`;

export const StyledFeatureCard = styled(Card)`
  border-radius: 18px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
  min-height: 170px;
  background: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  display: flex;
  justify-content: space-between;
  flex-direction: column;
  align-items: flex-start;
  padding: 0px !important;
  transition: box-shadow 0.18s;
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
  }
`;

export const StyledIconCircle = styled.div<{ $bg?: string }>`
  width: 45px;
  height: 45px;
  border-radius: 8px;
  background: ${({ $bg }) => $bg || '#f4f4fd'};
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  font-size: 20px;
`;

export const StyledCardTitle = styled(Title).attrs({ level: 5 })`
  padding-top: 10px !important;
  font-weight: 700 !important;
  color: #23263b !important;
  // margin: 0 0 8px;
  text-align: left;
`;

export const StyledCardDesc = styled(Paragraph)`
  color: #7d8597;
  font-size: 0.9rem;
  // margin-top: px !important;
  text-align: left;
`;
