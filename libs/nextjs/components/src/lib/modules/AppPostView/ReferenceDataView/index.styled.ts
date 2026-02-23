import styled from 'styled-components';

export const StyledContainer = styled.div`
  padding: 8px 12px;
  margin-bottom: 12px;
  cursor: pointer;
  position: relative;
  background-color: ${({theme}) => theme.palette.background.component};
  border-radius: 8px;
`;

export const StyledParent = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;

  & .ant-typography {
    margin-bottom: 0 !important;
    flex: 1;
  }
`;
