import styled from 'styled-components';
import { Button, Card, Row, Typography } from 'antd';

const { Title, Text } = Typography;

export const StyledCallActionSection = styled.section`
  width: 100%;
  min-height: 420px;
  background: linear-gradient(120deg, #377dff 0%, #a259e6 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 72px 0 56px 0;
  position: relative;
  box-sizing: border-box;
`;

export const StyledCallActionHeading = styled(Title).attrs({ level: 2 })`
  && {
    color: #fff;
    font-weight: 800;
    font-size: 2.8rem;
    text-align: center;
    line-height: 1.15;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
     @media (max-width: 768px) {
      font-size: 1.9rem;
  }
`;

export const StyledCallActionSubtitle = styled(Text)`
  && {
    color: #fff;
    font-size: 1.1rem;
    text-align: center;
    opacity: 0.97;
    margin-bottom: 38px;
    display: block;
     @media (max-width: 768px) {
     margin-bottom: 0px;}
`;

export const StyledCallActionStatRow = styled(Row)`
  margin-bottom: 36px !important;
`;

export const StyledCallActionStatCard = styled(Card)`
  background: rgba(255, 255, 255, 0.12) !important;
  border: none !important;
  border-radius: 16px !important;
  width: 100%;
  min-height: 110px;
  box-shadow: none !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff !important;

  @media (max-width: 768px) {
    width: 100%;
    min-width: 0;
    max-width: 100%;
  }

  &.ant-card .ant-card-body {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
`;

export const StyledCallActionStatNumber = styled.div`
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  margin-top: 8px;
  margin-bottom: 2px;
`;

export const StyledCallActionStatLabel = styled.div`
  color: #e8e8e8;
  font-size: 0.98rem;
  opacity: 0.85;
`;

export const StyledCallActionButtonWrapper = styled.div`
  display: flex;
  justify-content: center;
  margin: 18px 0 0 0;
`;

export const StyledCallActionCTAButton = styled(Button)`
  background: #fff !important;
  color: #377dff !important;
  border: none !important;
  font-weight: 600;
  font-size: 1.08rem;
  min-width: 230px;
  height: 44px;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.1);
  transition: all 0.18s;
  &:hover {
    background: #f5f6fa !important;
    color: #377dff !important;
  }
`;

export const StyledCallActionNote = styled.div`
  color: #fff;
  opacity: 0.65;
  font-size: 0.95rem;
  text-align: center;
  margin-top: 16px;
`;
