import styled from 'styled-components';
import { Typography } from 'antd';

const { Text, Paragraph } = Typography;

export const StyledFlexContainer = styled.div`
  display: flex;
  margin: 0 !important;
  justify-content: flex-start;
  gap: 8px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
  }
`;

export const StyledLabel = styled(Text)`
  width: 200px;
  margin: 0 !important;
`;

export const StyledValue = styled(Paragraph)`
  flex: 1;
  min-width: 0;
  margin: 0 !important;
  text-align: left;
  font-weight: ${({ theme }) => theme.font.weight.medium};
`;
