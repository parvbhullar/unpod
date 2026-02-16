import styled from 'styled-components';
import { Input } from 'antd';

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  width: 320px;
  border-radius: ${({ theme }) => theme.component.card.borderRadius}
    ${({ theme }) => theme.component.card.borderRadius} 0 0;
  display: flex;
  overflow: hidden;
  flex-direction: column;
  position: relative;
`;

export const StyledStickyContainer = styled.div`
  background-color: ${({ theme }) => theme.palette.background.default};
  position: sticky;
  top: 0;
  z-index: 1;
`;

export const StyledHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 16px;
`;

export const StyledTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: ${({ theme }) => theme.palette.primary};

  & .ant-typography {
    color: ${({ theme }) => theme.palette.primary};
  }
`;

export const StyledActionContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
`;

export const StyledInput = styled(Input)`
  //border-radius: 10px;
`;

export const StyledMenuContainer = styled.div`
  flex: 1;
  overflow-y: auto;
`;
