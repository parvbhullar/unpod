import styled from 'styled-components';
import SimpleBar from 'simplebar-react';

export const StyledRoot = styled.div`
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 0 16px;
`;

export const StyledScrollbar = styled(SimpleBar)`
  height: calc(100vh - 64px);

  .simplebar-content {
    display: flex;
    flex-direction: column;
    min-height: calc(100vh - 64px);
    position: relative;
  }
`;
