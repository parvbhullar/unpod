import styled from 'styled-components';
import { Tag } from 'antd';

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  flex: 1;
  height: calc(100vh - 74px);
  overflow-y: hidden;
`;

export const StyledContainer = styled.div`
  padding: 16px;
`;

export const StyledTag = styled(Tag)`
  text-transform: capitalize;
`;
