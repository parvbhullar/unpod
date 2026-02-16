import styled from 'styled-components';

export const StyledContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  // height: calc(100vh - 64px);
  // overflow: hidden;
  width: 100%;
  background-image: linear-gradient(
    90deg,
    rgba(138, 119, 255, 0.14) 50%,
    rgba(245, 136, 255, 0.14) 100%
  );
  background-color: rgba(245, 136, 255, 0.14);
  border-radius: 14px 14px 0 0;
`;

export const StyledInnerContainer = styled.div`
  display: flex;
  flex-direction: column;
  // overflow: auto;
  padding: 5px;
  width: 100%;
  max-width: calc(100vw - 72px);
  // height: 100%;
  flex: 1;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    max-width: calc(100vw - 60px);
  }
`;
