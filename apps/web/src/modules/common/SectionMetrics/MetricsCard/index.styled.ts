import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph } = Typography;

export const StyledContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  align-self: center;
  gap: 10px;
  border: 1px solid ${({ theme }) => theme.palette.primaryActive};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 16px;
  text-align: center;
  width: 210px;
`;

export const StyledTitle = styled.div`
  font-weight: 600;
  font-size: 32px;
  color: ${({ theme }) => theme.palette.primary};
`;

export const StyledParagraph = styled(Paragraph)`
  font-size: 16px;
  margin-bottom: 0 !important;
`;

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  min-height: 140px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    min-height: auto;
  }
`;
