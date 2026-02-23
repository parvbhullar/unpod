import styled from 'styled-components';

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: row;
  height: 100%;
  width: 100%;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    flex-direction: column;
  }
`;

export const StyledCenterView = styled.div`
  flex: 1 1 0;
  height: 100%;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    flex: 2 1 0;
  }
`;

export const StyledImage = styled.img`
  width: 100%;
  height: auto;
  border-radius: 0.5rem;
`;

export const StyledSidePaneContainer = styled.div`
  display: flex;
  flex: 0 0 20%;

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    flex: 0 0 25%;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    flex: 1 1 0;
  }
`;

export const StyledInnerContainer = styled.div`
  display: flex;
  align-items: flex-end;
  flex: 1 1 0;
`;
