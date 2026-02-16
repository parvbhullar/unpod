import styled from 'styled-components';
import { Layout } from 'antd';

export const StyledLayout = styled(Layout)`
  display: flex;
  flex-direction: column;
  min-width: 0;
  width: 100%;
  position: relative;
  background: transparent;

  & .main-content {
    // background: url('/images/content-bg.png') repeat-y center center fixed;
  }
`;
