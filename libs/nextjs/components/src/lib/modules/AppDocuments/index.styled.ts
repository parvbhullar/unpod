import styled from 'styled-components';
import { Row } from 'antd';

export const StyledRow = styled(Row)`
  padding: 16px;
  min-height: 50%;
`;

export const StyledRootContainer = styled.div`
  flex: 1;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  //height: calc(100vh - 120px);
  height: calc(100vh - 172px);
  overflow-y: auto;

  & .email-item:last-child {
    border-block-end: none;
  }
`;
