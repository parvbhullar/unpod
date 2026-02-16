import React, { useRef, useState } from 'react';
import screenfull from 'screenfull';
import {
  selectLocalPeerID,
  selectPeerByID,
  selectScreenShareAudioByPeerID,
  selectScreenShareByPeerID,
  useHMSStore,
} from '@100mslive/react-sdk';
import TileMenu from '../TileMenu';
import { useIsHeadless, useUISettings } from '../../AppData/useUISettings';
import { UI_SETTINGS } from '../../common/constants';
import {
  Container,
  Info,
  Root,
  StyledMenuWrapper,
} from './VideoTile/index.styled';
import { Video } from './VideoTile';
import { ImShrink2 } from 'react-icons/im';
import { FaExpandAlt } from 'react-icons/fa';
import { getVideoTileLabel } from '../../common/utils';
import { Button } from 'antd';

const labelStyles = {
  position: 'unset',
  width: '100%',
  textAlign: 'center',
  transform: 'none',
  mt: '$2',
  flexShrink: 0,
};

const Tile = ({ peerId, width = '100%', height = '100%' }) => {
  const isLocal = useHMSStore(selectLocalPeerID) === peerId;
  const track = useHMSStore(selectScreenShareByPeerID(peerId));
  const peer = useHMSStore(selectPeerByID(peerId));
  const isAudioOnly = useUISettings(UI_SETTINGS.isAudioOnly);
  const isHeadless = useIsHeadless();
  const [isMouseHovered, setIsMouseHovered] = useState(false);
  const showStatsOnTiles = useUISettings(UI_SETTINGS.showStatsOnTiles);
  const label = getVideoTileLabel({
    peerName: peer.name,
    isLocal: false,
    track,
  });
  const fullscreenRef = useRef(null);
  // fullscreen is for desired state
  const [isFullscreen, setFullscreen] = useState(false);
  // isFullscreen is for true state
  // const isFullscreen = useFullscreen(fullscreenRef, fullscreen, {
  //   onClose: () => setFullscreen(false),
  // });
  const isFullScreenSupported = screenfull.isEnabled;
  const audioTrack = useHMSStore(selectScreenShareAudioByPeerID(peer?.id));
  return (
    <Root css={{ width, height }} data-testid="screenshare_tile">
      {peer ? (
        <Container
          transparentBg
          ref={fullscreenRef}
          css={{ flexDirection: 'column' }}
          onMouseEnter={() => setIsMouseHovered(true)}
          onMouseLeave={() => {
            setIsMouseHovered(false);
          }}
        >
          {showStatsOnTiles ? (
            <div>
              VideoTileStats
              {/*
            <VideoTileStats
              audioTrackID={audioTrack?.id}
              videoTrackID={track?.id}
              peerID={peerId}
              isLocal={isLocal}
            />*/}
            </div>
          ) : null}
          {isFullScreenSupported && !isHeadless ? (
            <Button
              onClick={() => setFullscreen(!isFullscreen)}
              icon={isFullscreen ? <ImShrink2 /> : <FaExpandAlt />}
            />
          ) : null}
          {track ? (
            <Video
              screenShare={true}
              mirror={peer.isLocal && track?.source === 'regular'}
              attach={!isAudioOnly}
              trackId={track.id}
            />
          ) : null}
          <Info css={labelStyles}>{label}</Info>
          {isMouseHovered && !isHeadless && !peer?.isLocal ? (
            <StyledMenuWrapper>
              <TileMenu
                isScreenshare
                peerID={peer?.id}
                audioTrackID={audioTrack?.id}
                videoTrackID={track?.id}
              />
            </StyledMenuWrapper>
          ) : null}
        </Container>
      ) : null}
    </Root>
  );
};

const ScreenshareTile = React.memo(Tile);

export default ScreenshareTile;
