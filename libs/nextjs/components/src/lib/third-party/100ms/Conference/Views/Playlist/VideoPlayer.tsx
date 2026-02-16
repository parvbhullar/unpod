import React, { useRef } from 'react';
import { useFullscreen, useToggle } from 'react-use';
import {
  selectVideoPlaylist,
  selectVideoPlaylistAudioTrackByPeerID,
  selectVideoPlaylistVideoTrackByPeerID,
  useHMSActions,
  useHMSStore,
} from '@100mslive/react-sdk';
// import { VideoPlaylistControls } from './PlaylistControls';
import { useUISettings } from '../../../AppData/useUISettings';
import { UI_SETTINGS } from '../../../common/constants';
import { Button } from 'antd';
import { Video } from '../VideoTile';
import { AiOutlineCloseCircle } from 'react-icons/ai';

export const VideoPlayer = React.memo(({ peerId }) => {
  const videoTrack = useHMSStore(selectVideoPlaylistVideoTrackByPeerID(peerId));
  const audioTrack = useHMSStore(selectVideoPlaylistAudioTrackByPeerID(peerId));
  const active = useHMSStore(selectVideoPlaylist.selectedItem);
  const isAudioOnly = useUISettings(UI_SETTINGS.isAudioOnly);
  const hmsActions = useHMSActions();
  const ref = useRef(null);
  const [show, toggle] = useToggle(false);
  const isFullscreen = useFullscreen(ref, show, {
    onClose: () => toggle(false),
  });
  const showStatsOnTiles = useUISettings(UI_SETTINGS.showStatsOnTiles);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        width: '100%',
        height: '100%',
      }}
      ref={ref}
    >
      {active && (
        <div
          css={{
            padding: '8px 8px 8px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderTopLeftRadius: 4,
            borderTopRightRadius: 4,
          }}
        >
          <div css={{ color: '$textPrimary' }}>{active.name}</div>
          <Button
            css={{
              color: '$white',
            }}
            onClick={() => {
              hmsActions.videoPlaylist.stop();
            }}
            data-testid="videoplaylist_cross_btn"
            icon={<AiOutlineCloseCircle />}
          ></Button>
        </div>
      )}
      {showStatsOnTiles ? (
        <div>
          VideoTileStats
          {/*<VideoTileStats*/}
          {/*  audioTrackID={audioTrack?.id}*/}
          {/*  videoTrackID={videoTrack?.id}*/}
          {/*  peerID={peerId}*/}
          {/*  isLocal={active}*/}
          {/*/>*/}
        </div>
      ) : null}
      <Video
        trackId={videoTrack?.id}
        attach={!isAudioOnly}
        css={{
          objectFit: 'contain',
          h: 'auto',
          r: '$1',
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
        }}
      />
      {/*<VideoPlaylistControls>*/}
      {/*  {screenfull.enabled && (*/}
      {/*    <Button*/}
      {/*      onClick={() => toggle()}*/}
      {/*      style={{*/}
      {/*        color: 'white',*/}
      {/*        height: 'max-content',*/}
      {/*        alignSelf: 'center',*/}
      {/*        cursor: 'pointer',*/}
      {/*      }}*/}
      {/*      icon={isFullscreen ? <ImShrink2 /> : <FaExpandAlt />}*/}
      {/*    />*/}
      {/*  )}*/}
      {/*</VideoPlaylistControls>*/}
    </div>
  );
});
