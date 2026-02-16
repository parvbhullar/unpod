import styled from 'styled-components';
import { Layout } from 'antd';

const { Footer } = Layout;

export const StyledFooter = styled(Footer)`
  padding: 40px 50px !important;
  margin: 0 75px;
  background-color: ${({ theme }) =>
    theme.palette.background.default} !important;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    padding: 20px 30px !important;
  }
  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    padding: 20px 0px !important;
    margin: 0;
  }
`;

export const StyledFooterContainer = styled.div`
  max-width: 1600px;
  margin: 0 auto;
`;

export const StyledContact = styled.div`
  margin: 0;
`;

export const StyledLinkWrapper = styled(StyledContact)`
  display: flex;
  gap: 8px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-wrap: wrap;
  }
`;

export const StyledCopyright = styled.div`
  .ant-typography {
    margin-bottom: 0 !important;
    color: ${({ theme }) => theme.palette.text.heading} !important;
    font-weight: 500 !important;
    font-family: 'Onest', sans-serif;
  }
`;

export const StyledBottomContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    justify-content: center;
  }
`;
