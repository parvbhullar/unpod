import styled from 'styled-components';

export const StyledRoot = styled.div`
  padding: 20px 16px 16px 16px;
`;

export const StyledActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  position: sticky;
  bottom: 35px;
  padding-bottom: 10px;
  padding-top: 10px;
  background-color: ${({ theme }) => theme.palette.background.default};
  z-index: 3;
`;
