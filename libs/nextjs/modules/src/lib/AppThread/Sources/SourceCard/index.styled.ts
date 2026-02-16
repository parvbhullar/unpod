import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;
export const StyledRoot = styled.div`
  padding: 10px;
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.palette.background.component};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  height: 100%;
  min-height: 90px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: ${({ theme }) => theme.palette.background.colorPrimaryBg};
  }
`;

export const StyledParagraph = styled(Paragraph)`
  flex: 1;
`;
