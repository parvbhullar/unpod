import styled from 'styled-components';
import { Button, Typography } from 'antd';

const { Title, Paragraph } = Typography;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  flex: 1;
`;

export const StyledMainInfo = styled.div`
  text-align: center;
  max-width: 760px;
  margin: 0 auto;
`;

export const StyledHeading = styled(Title)`
  font-size: 28px !important;
  font-weight: 700 !important;
`;

export const StyledDescription = styled(Paragraph)`
  font-size: 16px;
  font-weight: 500;
`;

export const StyledSectionCard = styled.div`
  background: linear-gradient(to right, #f5f0ff, #eef6ff);
  padding: 24px;
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  margin-bottom: 8px;
`;

export const StyledSectionTitle = styled(Title)`
  font-size: 22px !important;
  margin-bottom: 8px;
`;

export const StyledSectionParagraph = styled(Paragraph)`
  font-size: 16px;
  margin-bottom: 0 !important;
`;

export const StyledGetStartedButton = styled(Button)`
  background: linear-gradient(to right, #9254de, #1890ff);
  border: none;
  color: white;
  padding: 10px 24px;
  flex-direction: row-reverse;

  &:hover {
    background: linear-gradient(to right, #7b3fb7, #1373cc) !important;
  }
`;
