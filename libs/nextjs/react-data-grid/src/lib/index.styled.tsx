import styled from 'styled-components';
import { Space } from 'antd';

/*export const StyledTableWrapper = styled.div`
  position: relative;
`;

export const StyledTableEmptyWrapper = styled.div`
  position: sticky;
  left: 0;
  grid-column: 1/-1;
  text-align: center;
  padding-block: 50px;
`;*/

export const StyledTableWrapper = styled.div`
  position: relative;
`;

export const StyledTableEmptyWrapper = styled.div`
  position: sticky;
  left: 0;
  grid-column: 1/-1;
  text-align: center;
  padding-block: 50px;
`;

export const StyledTableActions = styled(Space)`
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: center;

  &.align-right {
    justify-content: flex-end;
  }
  & .ant-space-item {
    display: inline-flex;
    align-items: center;
  }
`;
