import styled from 'styled-components';
import {Avatar} from 'antd';

const getAvatarShape = (radius) => {
  return radius;
};
export const Root = styled.div`
  padding: 0.75rem;
`;
export const Container = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  border-radius: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #bfbfbf;
`;

export const Overlay = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
`;

export const Info = styled.div`
  color: ${({theme}) => theme.palette.text.primary};
  position: absolute;
  bottom: 5px;
  left: 50%;
  font-size: 12px;
  transform: translateX(-50%);
  text-align: center;
  width: 80%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`;

export const AttributeBox = styled.div`
  position: absolute;
  color: ${({theme}) => theme.palette.text.primary};
`;

export const AudioIndicator = styled(Avatar)`
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #33333333;
  top: 8px;
  right: 8px;
  color: white;
  border-radius: 50%;
  /*width: 40px;
  height: 40px;*/
`;
export const StyledMenuWrapper = styled(Avatar)`
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #33333333;
  cursor: pointer;
  bottom: 8px;
  right: 8px;
  color: white;
  border-radius: 50%;
  /*width: 40px;
  height: 40px;*/
  z-index: 101;
  opacity: ${({$isMouseHovered}) => ($isMouseHovered ? 1 : 0)};
  transition: opacity 0.2s ease-in;
`;

export const StyledRaiseHand = styled(AudioIndicator)`
  top: 8px;
  left: 8px;
  background-color: ${({theme}) => theme.palette.primary};
`;

export const StyledBRB = styled.div`
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  top: 8px;
  left: 8px;
  font-size: 0.8rem;
  background: #33333333;
  color: white;
  // height: 42px;
  padding: 0.35rem;
  border-radius: 8px;
  border: 1px solid #fff;
`;

export const FullScreenButton = styled.button`
  width: 2.25rem;
  height: 2.25rem;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 5;
`;

/*export const AvatarContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translateX(-50%) translateY(-50%);
  width: 40%;
  height: 40%;
  & > div {
    max-height: 20px;
    height: 100%;
  }
`;*/

export const StyledAvatar = styled.div`
  color: white;
  aspect-ratio: 1;
  font-weight: 600;
`;
export const StyledVideo = styled.video`
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 16px;
  object-fit: cover;
  background: #dfdfdf;
`;
