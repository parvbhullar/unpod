import styled from 'styled-components';

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    flex-direction: column;
  }
`;

export const StyledVideoContainer = styled.div`
  flex: 1 1 0;
`;

export const StyledImage = styled.img`
  width: 100%;
  height: auto;
  border-radius: 0.5rem;
`;

export const StyledRoot = styled.div`
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
`;

export const StyledViewContainer = styled.div`
  height: 100%;
  width: 100%;
  position: relative;
  display: flex;
  // align-items: center;
  overflow: auto;
`;

export const StyledView = styled.div`
  height: 100%;
  width: 100%;
  position: absolute;
  display: flex;
  place-content: center;
  flex-wrap: wrap;
  align-items: center;
`;
