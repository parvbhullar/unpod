import styled, { keyframes } from 'styled-components';

export const StyledRoot = styled.div`
  margin: 0 auto 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: margin 0.8s;
  overflow: hidden;
`;

export const scroll = keyframes`
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); } /* move half because we doubled list */
`;

export const StyledMarquee = styled.div`
  overflow: hidden;
  white-space: nowrap;
  display: flex;
  align-items: center;
`;

export const StyledTrack = styled.div`
  display: flex;
  animation: ${scroll} 35s linear infinite;

  &:hover {
    animation-play-state: paused;
  }
`;

export const StyledLogoWrapper = styled.div`
  flex: 0 0 auto;
  height: 100px;
  min-width: 100px;
  width: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-right: 80px;

  img {
    height: 100%;
    width: auto;
    object-fit: contain;
    display: block;
    border-radius: 12px;
  }
`;
