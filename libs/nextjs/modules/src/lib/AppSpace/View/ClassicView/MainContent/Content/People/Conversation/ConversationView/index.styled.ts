import styled from 'styled-components';

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.palette.background.default};
  overflow-y: auto;
  scrollbar-width: thin;
`;

export const StyledInnerContainer = styled.div`
  position: relative;
`;

export const StyledMoreContainer = styled.div`
  display: flex;
  justify-content: center;
  padding-top: 24px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding-top: 0;
  }
`;
