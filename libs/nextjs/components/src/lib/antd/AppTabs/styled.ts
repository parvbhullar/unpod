import {Tabs} from 'antd';
import styled from 'styled-components';

export const StyledTabs = styled(Tabs)`
  .ant-tabs-content {
    padding: 12px;
  }
  .ant-drawer-body & .ant-tabs-content {
    padding: 0 !important;
  }
  .ant-drawer-body & .ant-tabs-content {
    padding: 0;
  }
`;
