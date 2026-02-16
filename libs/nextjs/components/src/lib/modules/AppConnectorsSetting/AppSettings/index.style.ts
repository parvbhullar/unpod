import styled from 'styled-components';

export const StyledRoot = styled.div`
  background-color: ${({ theme }) => theme.palette.primaryHover};
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 24px;
  margin-bottom: 24px;
`;

export const StyledTitleWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;
