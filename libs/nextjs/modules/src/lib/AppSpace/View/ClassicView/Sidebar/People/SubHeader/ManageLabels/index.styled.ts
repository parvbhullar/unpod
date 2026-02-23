import styled from 'styled-components';
import {Tabs} from 'antd';

export const StyledTabs = styled(Tabs)`
  background-color: ${({theme}) => theme.palette.background.default};
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 16px 24px 0 24px;

  .ant-tabs-nav {
    margin-bottom: 0;
  }

  .ant-tabs-nav-more {
    margin-left: 0 !important;
  }
`;

export const StyledTagContainer = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  background-color: ${({theme}) => theme.palette.background.component};
  border-bottom: 1px solid ${({theme}) => theme.border.color};
  padding: 8px 16px;

  &:hover {
    background-color: ${({theme}) => theme.palette.primaryHover};
  }
`;
export const StyledRoot = styled.div`
  padding: 16px 24px 0;
`;

export const StyledWrapper = styled.div`
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: 10px;
  overflow: hidden;

  & ${StyledTagContainer}:last-child {
    border-bottom: none;
  }
`;

export const StyledContent = styled.div`
  flex: 1;
  min-width: 230px;
  display: flex;
  align-items: center;
`;
