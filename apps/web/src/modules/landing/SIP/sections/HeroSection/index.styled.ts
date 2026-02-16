import styled from 'styled-components';
import { Button, Typography } from 'antd';

// Ensure Typography components are imported
const { Text, Title, Paragraph } = Typography;

export const StyledPillTag = styled(Text)`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(
    90deg,
    rgba(55, 125, 255, 0.15) 0%,
    rgba(168, 57, 255, 0.15) 100%
  );
  color: ${({ theme }) => theme.palette.text.heading};
  font-size: 0.9rem;
  border-radius: 999px;
  padding: 6px 12px;
  margin: 0 auto 32px;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.04);
`;

export const StyledHeadline = styled(Title).attrs({ level: 1 })`
  font-size: 3.2rem !important;
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.text.heading};
  line-height: 1.15;
  text-align: center;
  margin: 0 auto 16px !important;
  @media (max-width: 768px) {
    font-size: 2.8rem !important;
  }
`;

export const StyledHighlight = styled.span`
  display: block;
  font-size: 3.2rem;
  font-weight: ${({ theme }) => theme.font.weight.bold};
  color: ${({ theme }) => theme.palette.primary};
  text-align: center;
  @media (max-width: 768px) {
    font-size: 2.8rem;
  }
`;

export const StyledSubtitle = styled(Paragraph)`
  && {
    color: ${({ theme }) => theme.palette.text.heading};
    font-size: 1.4rem;
    font-weight: 400;
    letter-spacing: 0.01em;
    line-height: 1.35;
    max-width: 720px;
    text-align: center;
    margin: 0 auto 40px !important;

    @media (max-width: 700px) {
      font-size: 1rem;
      margin-bottom: 24px !important;
    }
  }
`;

export const StyledButtonRow = styled.div`
  display: flex;
  gap: 18px;
  justify-content: center;
  margin: 0 auto 48px;
  flex-wrap: wrap;
`;

export const StyledFeatureRow = styled.div`
  display: flex;
  gap: 30px;
  justify-content: center;
  // margin: 0 auto 60px;
  flex-wrap: wrap;
  @media (max-width: 700px) {
    flex-direction: column;
    align-items: center;
  }
`;

export const StyledFeatureTag = styled.div`
  display: flex;
  align-items: center;
  gap: 7px;
  color: #7d8597;
  background: none;
  font-size: 0.8rem;
  font-weight: 500;
`;

export const StyledCenterSection = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
`;
export const StyledPrimaryButton = styled(Button)`
  background: linear-gradient(90deg, #377dff 0%, #a839ff 100%) !important;
  color: #fff !important;
  font-weight: 500 !important;
  font-size: 16px !important;
  padding: 16px 32px !important;
  min-width: 248px;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.1) !important;
`;

export const StyledSecondaryButton = styled(Button)`
  font-weight: 600 !important;
  font-size: 16px !important;
  padding: 16px 32px !important;
  min-width: 205px;
  box-shadow: 0 2px 8px rgba(80, 80, 120, 0.1) !important;
`;
