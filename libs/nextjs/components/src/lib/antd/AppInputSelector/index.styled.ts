import styled from 'styled-components';
import {Divider} from 'antd';

export const StyledList = styled.ul`
  padding: 0;
  margin: 0;
  min-width: 280px;
  width: 100%;
  max-height: 50vh;
  overflow-y: auto;
  scrollbar-width: thin;
`;
export const StyledListItem = styled.li`
  padding: 5px 8px;
  cursor: pointer;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;

  &:hover {
    background: lavender;
  }
`;

export const StyledDivider = styled(Divider)`
  margin: 0;
`;
