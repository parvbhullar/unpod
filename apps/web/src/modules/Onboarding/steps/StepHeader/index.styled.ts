import styled from 'styled-components';
import { Typography } from 'antd';

const { Paragraph, Title } = Typography;

export const StyledRoot = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 10px !important;
  margin-right: 130px;

  .ant-typography {
    font-family: ${({ theme }) => theme.font.family} !important;
    margin: 0 !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin-left: 50px;
    padding: 0 !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    padding: 10px !important;
  }
`;

export const StyledTitle = styled(Title)`
  font-size: 18px !important;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    font-size: 16px !important;
  }
  @media (max-width: ${({ theme }) => theme.breakpoints.xs}px) {
    display: none;
  }
`;

export const StyledParagraph = styled(Paragraph)`
  font-size: 13px !important;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    display: none;
  }
`;
