import styled from 'styled-components';
import {Button, Flex} from 'antd';

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: column;
  scrollbar-width: none;
  padding: 12px 0 0 0;
`;

export const StyledSearchBoxWrapper = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 6px;
  background: ${({theme}) => theme.palette.background.paper};
  border-bottom: ${({theme}) => theme.border.width} ${({theme}) => theme.border.style} ${({theme}) => theme.border.color};

  & > *:first-child {
    flex: 1;
    min-width: 150px !important;
    max-width: 300px;
  }
`;

export const StyledFlex = styled(Flex)`
  padding: 10px;
  border-radius: ${({theme}) => theme.radius.base}px;
  border: ${({theme}) => theme.border.width}
    ${({theme}) => theme.border.style} ${({theme}) => theme.border.color};
  margin-bottom: 12px;

  &:hover {
    border-color: ${({theme}) => theme.palette.primary};
    cursor: pointer;
  }

  &.active {
    border-color: ${({theme}) => theme.palette.primary};
  }
`;

export const StyledButton = styled(Button)`
  height: 28px;

  &.ant-btn-circle {
    width: 28px;
    min-width: 28px !important;
  }
`;
