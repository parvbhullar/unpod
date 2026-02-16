import styled from 'styled-components';

export const StyledPagination = styled.div`
  height: 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;

  & > * + * {
    margin-right: 0;
    margin-left: 0.5rem;
  }
`;
