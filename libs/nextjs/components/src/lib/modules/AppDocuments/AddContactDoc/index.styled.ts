import styled from 'styled-components';
import {Tabs, Upload} from 'antd';

const {Dragger} = Upload;

export const StyledRoot = styled.div`
  flex: 1;
`;

export const StyledTabs = styled(Tabs)`
  background-color: ${({theme}) => theme.palette.background.default};
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 16px 16px 0 16px;

  .ant-tabs-nav {
    margin-bottom: 0;
  }

  .ant-tabs-nav-more {
    margin-left: 0 !important;
  }
`;

export const StyledContainer = styled.div`
  padding: 16px;
`;

export const StyledDragger = styled(Dragger)`
  display: inline-flex;
  flex-direction: column;
  width: 100%;
  border-radius: 8px;
  margin-bottom: 16px;

  .ant-upload-drag {
    border-width: 2px;
  }

  .ant-upload-btn {
    padding: 16px !important;
  }
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
`;

export const StyledActionsWrapper = styled.div`
  display: flex;
  gap: 16px;
  flex-direction: column;
`;
