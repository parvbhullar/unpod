import styled from 'styled-components';

export const StyledContainer = styled.div`
  width: 100%;
  max-width: 860px;
  margin: 60px auto 0 auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    margin: 30px auto 0 auto;
  }
`;

export const StyledListContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  grid-gap: 10px;

  @media screen and (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
    grid-gap: 20px;
  }
`;
