import styled from 'styled-components';

export const StyledRoot = styled.div`
  width: 100%;
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth});
  background-color: ${({ theme }) => theme.palette.background.default};
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  border-radius: 12px 12px 0 0;

  @media (max-width: ${({ theme }) => theme.breakpoints.xl}px) {
    padding: 14px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding: 8px 10px;
  }
`;
