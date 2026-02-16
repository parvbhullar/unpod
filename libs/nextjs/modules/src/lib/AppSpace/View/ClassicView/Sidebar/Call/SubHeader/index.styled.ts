import styled from 'styled-components';
import { Space } from 'antd';

export const StyledRoot = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px 7px 10px;
  border-bottom: 1px solid ${({ theme }) => theme.border.color};
  background-color: ${({ theme }) => theme.palette.background.default};
  z-index: 2;
`;

export const StyledSearchBoxWrapper = styled.div`
  width: 230px !important;
`;

export const StyledContent = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
`;

export const StyledSpace = styled(Space)`
  align-items: flex-end;
  .ant-btn-text {
    color: ${({ theme }) => theme.palette.text.secondary};
    &:hover,
    &.active {
      color: ${({ theme }) => theme.palette.primary};
    }
  }
`;

export const StyledFilterContent = styled.div`
  opacity: 0;
  height: 0;
  overflow: hidden;
  transform: translateY(-50px);
  transition: all 0.3s ease;
  z-index: 1;

  &.active {
    opacity: 1;
    height: calc(-121px + 100vh);
    //height: 100vh;
    overflow-y: auto;
    transform: translateX(0);
    scrollbar-width: thin;
  }
`;
