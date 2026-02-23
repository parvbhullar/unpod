import styled from 'styled-components';
import MuxPlayer from '@mux/mux-player-react';
import {Typography} from 'antd';

export const StyledMuxPlayer = styled(MuxPlayer)`
  width: 100%;
  // max-width: 100%;
  // margin-bottom: 20px;
  /*border-radius: ${({theme}) => theme.radius.base}px;
  overflow: hidden;*/

  /*&.audio-player {
    --secondary-color: ${({theme}) => theme.palette.primary};
    --media-background-color: ${({theme}) => theme.palette.primary};
    --media-control-background: ${({theme}) => theme.palette.primary};

    .media-controller {
      background-color: ${({theme}) => theme.palette.primary} !important;
    }
  }*/

  &.video-player {
    margin-bottom: 20px;
    aspect-ratio: 16 / 9;
    border-radius: ${({theme}) => theme.radius.base}px;
    overflow: hidden;
  }

  &.audio-player {
    --media-object-fit: cover;
    --media-object-position: center;
    background-color: rgba(0, 0, 0, 0.85);
    border-radius: ${({theme}) => theme.radius.base}px;
    overflow: hidden;
    padding-right: 2px;

    /*--seek-live-button: none;
    --seek-backward-button: none;
    --seek-forward-button: none;
    --time-range: none;*/

    /*--seek-backward-button: none;
    --seek-forward-button: none;
    --controls: none;*/

    /*--secondary-color: ${({theme}) => theme.palette.primary};
    --media-background-color: ${({theme}) => theme.palette.primary};
    --media-control-background: ${({theme}) => theme.palette.primary};

    --controls-backdrop-color: ${({theme}) => theme.palette.primary};

    .media-controller {
      background-color: ${({theme}) => theme.palette.primary} !important;
    }*/
  }
`;

export const StyledAudioTitle = styled(Typography.Title)`
  margin-bottom: 0 !important;
`;

export const StyledMeta = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

export const StyledAvatarWrapper = styled.div`
  margin: 0 8px 0 0;
  color: ${({theme}) => theme.palette.primary};

  * + * {
    margin-left: 6px;
  }
`;

export const StyledUserBar = styled.div`
  display: flex;
  min-width: 0;
  align-items: center;
  cursor: pointer;
`;

export const StyledMusicWrapper = styled.div`
  position: relative;
  height: 175px;
  width: 175px;
  border-radius: ${({theme}) => theme.radius.circle};
  overflow: hidden;
`;

export const StyledPlayerInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
`;

export const StyledPlayerBody = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
`;

export const StyledAudioPlayer = styled.div`
  position: relative;
  padding: 24px;
  margin-bottom: 20px;
  background-color: ${({theme}) => theme.palette.primary}33;
  border-radius: ${({theme}) => theme.radius.base}px;
`;

export const StyledCanvas = styled.canvas`
  width: 100%;
  height: 100px;
`;
