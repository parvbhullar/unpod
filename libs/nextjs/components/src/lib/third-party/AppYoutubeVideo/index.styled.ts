import styled from 'styled-components';

export const StyledVideoContainer = styled.div`
  position: relative;
  margin: 0 auto;
  min-height: 100px;
  max-width: 100%;
`;

export const StyledImageContainer = styled.div`
  position: relative;
  margin: 0 auto;
`;

export const StyledVideoWrapper = styled.div`
  position: absolute;
  height: 100%;
  top: 60px;
  left: -80px;
  right: -80px;
  bottom: 60px;

  & > div {
    position: relative;
    display: block;
    width: 100%;
    padding: 0;
    overflow: hidden;

    &::before {
      padding-top: 56.25%;
      display: block;
      content: '';
    }
  }

  & iframe {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 0;
  }
`;

export const StyledIPlayBtnWrapper = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &:before {
    content: '';
    width: 30px;
    height: 30px;
    position: absolute;
    background-color: ${({theme}) => theme.palette.background.default};
    z-index: 99;
  }

  &:hover .play-button {
    color: ${({theme}) => theme.palette.error};
  }

  & .play-button {
    color: ${({theme}) => theme.palette.common.black};
    height: 80px;
    width: 100px;
    z-index: 100;
  }
`;
