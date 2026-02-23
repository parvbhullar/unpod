import styled from 'styled-components';
import {Layout} from 'antd';

const {Header} = Layout;

export const StyledHeader = styled(Header)`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 10px 16px 16px !important;
  position: sticky;
  top: 0;
  width: 100%;
  z-index: 101;
  height: 64px;
  border-radius: 12px 12px 0 0;
  border-bottom: 1px solid ${({theme}) => theme.border.color};

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    padding: 10px 10px !important;
  }
`;

export const StyledRoot = styled.div`
  margin: 24px 0 0 0;
  padding: 0 24px;
`;

export const StylesImageWrapper = styled.div`
  position: relative;
  width: 100px;
  height: 100px;
  border: 1px solid ${({theme}) => theme.border.color};
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 12px;
  cursor: pointer;
`;

export const StyledTabWrapper = styled.div`
  .ant-tabs-nav {
    margin: 0 !important;
  }
`;

export const StyledEditContainer = styled.div`
  padding-top: 7px;
`;
