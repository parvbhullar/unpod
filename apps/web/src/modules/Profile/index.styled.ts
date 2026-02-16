import styled from 'styled-components';
import { Tabs } from 'antd';

export const StyledContainer = styled.div`
  position: relative;
  padding: 8px 16px 16px 16px;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius};
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  width: ${({ theme }) => theme.sizes.mainContentWidth};
  max-width: 100%;
  margin: 16px auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.md + 75}px) {
    margin: 0 auto;
  }
`;

export const StyledTabs = styled(Tabs)`
  .ant-tabs-nav {
    margin-bottom: 0;
    padding-inline: 20px;
  }
`;
