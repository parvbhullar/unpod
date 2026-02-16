import React, { useCallback, useMemo, useState, CSSProperties } from 'react';
import {
  selectAudioTrackByPeerID,
  selectIsPeerAudioEnabled,
  selectLocalPeerID,
  selectPeerMetadata,
  selectPeerNameByID,
  selectVideoTrackByID,
  selectVideoTrackByPeerID,
  useHMSStore,
  useVideo,
} from '@100mslive/react-sdk';
import { useIsHeadless, useUISettings } from '../../../AppData/useUISettings';
import { UI_SETTINGS } from '../../../common/constants';
import { useAppConfig } from '../../../AppData/useAppConfig';
import {
  AudioIndicator,
  Container,
  Root,
  StyledBRB,
  StyledMenuWrapper,
  StyledRaiseHand,
  StyledVideo,
} from './index.styled';
import TileConnection from '../../Connection/TileConnection';
import { getVideoTileLabel } from '../../../common/utils';
import TileMenu from '../../TileMenu';
import UserThumbnail from './UserThumbnail';
import { MdMicOff } from 'react-icons/md';
import { TbHandStop } from 'react-icons/tb';

type TileSize = 'small' | 'medium';
type AvatarSize = 'small' | 'medium' | 'large';

interface PeerMetadataProps {
  peerId: string;
  size: TileSize;
}

const PeerMetadata: React.FC<PeerMetadataProps> = ({ peerId, size }) => {
  const metaData = useHMSStore(selectPeerMetadata(peerId));
  const isHandRaised = metaData?.isHandRaised || false;
  const isBRB = metaData?.isBRBOn || false;

  return (
    <>
      {isHandRaised ? (
        <StyledRaiseHand data-testid="raiseHand_icon_onTile" size={size}>
          <TbHandStop fontSize={20} />
        </StyledRaiseHand>
      ) : null}
      {isBRB ? <StyledBRB>BRB</StyledBRB> : null}
    </>
  );
};

interface VideoProps {
  trackId: string;
  attach?: boolean;
  mirror?: boolean;
  degraded?: boolean;
  noRadius?: boolean;
  'data-testid'?: string;
}

export const Video: React.FC<VideoProps> = ({ trackId, attach, ...props }) => {
  const { videoRef } = useVideo({ trackId, attach });
  return (
    <StyledVideo
      autoPlay
      muted
      playsInline
      controls={false}
      ref={videoRef}
      {...props}
    />
  );
};

interface ShowAudioMutedParams {
  hideTileAudioMute?: boolean;
  isHeadless: boolean;
  isAudioMuted: boolean;
}

const showAudioMuted = ({ hideTileAudioMute, isHeadless, isAudioMuted }: ShowAudioMutedParams): boolean => {
  if (!isHeadless) {
    return isAudioMuted;
  }
  return isAudioMuted && !hideTileAudioMute;
};

interface GetPaddingParams {
  isHeadless: boolean;
  tileOffset?: string | number;
  hideAudioLevel?: boolean;
}

const getPadding = ({ isHeadless, tileOffset, hideAudioLevel }: GetPaddingParams): number | undefined => {
  if (!isHeadless || isNaN(Number(tileOffset))) {
    return undefined;
  }
  // Adding extra padding of 3px to ensure that the audio border is visible properly between tiles when tileOffset is 0.
  return Number(tileOffset) === 0 ? (hideAudioLevel ? 0 : 3) : undefined;
};

interface VideoTileStatsProps {
  videoTrackID?: string;
  audioTrackID?: string;
  isLocal?: boolean;
  peerID?: string;
}

function VideoTileStats(props: VideoTileStatsProps) {
  return null;
}

interface VideoTileProps {
  peerId: string;
  trackId?: string;
  width?: number;
  height?: number;
  objectFit?: 'cover' | 'contain' | 'fill' | 'none' | 'scale-down';
  rootCSS?: CSSProperties;
  containerCSS?: CSSProperties;
}

const VideoTile: React.FC<VideoTileProps> = ({
  peerId,
  trackId,
  width,
  height,
  objectFit = 'cover',
  rootCSS = {},
  containerCSS = {},
}) => {
  const trackSelector = trackId
    ? selectVideoTrackByID(trackId)
    : selectVideoTrackByPeerID(peerId);
  const track = useHMSStore(trackSelector);
  const peerName = useHMSStore(selectPeerNameByID(peerId));
  const metaData = useHMSStore(selectPeerMetadata(peerId));
  const audioTrack = useHMSStore(selectAudioTrackByPeerID(peerId));
  const localPeerID = useHMSStore(selectLocalPeerID);
  const isAudioOnly = useUISettings(UI_SETTINGS.isAudioOnly);
  const mirrorLocalVideo = useUISettings(UI_SETTINGS.mirrorLocalVideo);
  const showStatsOnTiles = useUISettings(UI_SETTINGS.showStatsOnTiles);
  const isHeadless = useIsHeadless();
  const isAudioMuted = !useHMSStore(selectIsPeerAudioEnabled(peerId));
  const isVideoMuted = !track?.enabled;
  const [isMouseHovered, setIsMouseHovered] = useState(false);
  // const borderAudioRef = useBorderAudioLevel(audioTrack?.id);
  const isVideoDegraded = track?.degraded;
  const isLocal = localPeerID === peerId;
  const label = getVideoTileLabel({
    peerName,
    track,
    isLocal,
  });
  const onHoverHandler = useCallback((event: React.MouseEvent) => {
    setIsMouseHovered(event.type === 'mouseenter');
  }, []);
  const headlessConfig = useAppConfig('headlessConfig');
  const hideLabel = isHeadless && headlessConfig?.hideTileName;
  const isTileBigEnoughToShowStats = height && width && height >= 180 && width >= 180;

  const avatarSize = useMemo((): AvatarSize | undefined => {
    if (!width || !height) {
      return undefined;
    }
    if (width <= 150 || height <= 150) {
      return 'small';
    } else if (width <= 300 || height <= 300) {
      return 'medium';
    }
    return 'large';
  }, [width, height]);

  return (
    <Root
      style={{
        width,
        height,
        padding: getPadding({
          isHeadless,
          tileOffset: headlessConfig?.tileOffset,
          hideAudioLevel: headlessConfig?.hideAudioLevel,
        }),
        ...rootCSS,
      }}
      data-testid={`participant_tile_${peerName}`}
    >
      {peerName !== undefined ? (
        <Container
          onMouseEnter={onHoverHandler}
          onMouseLeave={onHoverHandler}
          ref={
            isHeadless && headlessConfig?.hideAudioLevel ? undefined : undefined //borderAudioRef
          }
          noRadius={isHeadless && Number(headlessConfig?.tileOffset) === 0}
          css={containerCSS}
        >
          {showStatsOnTiles && isTileBigEnoughToShowStats ? (
            <VideoTileStats
              audioTrackID={audioTrack?.id}
              videoTrackID={track?.id}
              peerID={peerId}
              isLocal={isLocal}
            />
          ) : null}
          {track ? (
            <Video
              trackId={track?.id}
              attach={isLocal ? undefined : !isAudioOnly}
              mirror={
                mirrorLocalVideo &&
                peerId === localPeerID &&
                track?.source === 'regular' &&
                track?.facingMode !== 'environment'
              }
              degraded={isVideoDegraded}
              noRadius={isHeadless && Number(headlessConfig?.tileOffset) === 0}
              data-testid="participant_video_tile"
              /*css={{
                objectFit,
              }}*/
            />
          ) : null}
          {isVideoMuted || isVideoDegraded || (!isLocal && isAudioOnly) ? (
            <UserThumbnail
              peerId={peerId}
              data-testid="participant_avatar_icon"
              avatarSize={avatarSize}
            />
          ) : null}
          {showAudioMuted({
            hideTileAudioMute: headlessConfig?.hideTileAudioMute,
            isHeadless,
            isAudioMuted,
          }) ? (
            <AudioIndicator
              data-testid="participant_audio_mute_icon"
              size={
                width && height && (width < 180 || height < 180)
                  ? 'small'
                  : 'medium'
              }
            >
              <MdMicOff fontSize={20} />
            </AudioIndicator>
          ) : null}

          {!isHeadless ? (
            <StyledMenuWrapper
              $isMouseHovered={isMouseHovered}
              size={
                width && height && (width < 180 || height < 180)
                  ? 'small'
                  : 'medium'
              }
            >
              <TileMenu
                peerID={peerId}
                audioTrackID={audioTrack?.id}
                videoTrackID={track?.id}
              />
            </StyledMenuWrapper>
          ) : null}
          <PeerMetadata
            peerId={peerId}
            size={
              width && height && (width < 180 || height < 180)
                ? 'small'
                : 'medium'
            }
          />

          <TileConnection
            hideLabel={hideLabel}
            name={label}
            isTile
            peerId={peerId}
            width={width}
            isMouseHovered={!trackId || (trackId && !isMouseHovered)}
          />
        </Container>
      ) : null}
    </Root>
  );
};

export default React.memo(VideoTile);
