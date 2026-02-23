import styled from 'styled-components';

export const StyledContainer = styled.div`
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    flex-direction: column;
  }
`;

export const StyledVideoContainer = styled.div`
  flex: 1 1 0;
  padding: 32px;
  min-height: 0;
  min-width: 0;
  display: flex;
  justify-content: center;
  align-items: center;
`;
