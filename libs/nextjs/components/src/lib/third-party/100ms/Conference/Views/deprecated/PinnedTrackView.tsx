import React from 'react';
import { useMeasure } from 'react-use';
import {
  selectPeers,
  selectVideoTrackByPeerID,
  useHMSStore,
} from '@100mslive/react-sdk';
import { GridSidePaneView } from '../MainGridView/GridView';
import VideoTile from '../VideoTile';
import { usePinnedTrack } from '../../../AppData/useUISettings';
import { StyledContainer } from '../index.styled';
import { useWindowSize } from '@unpod/custom-hooks';

const PinnedPeerView = () => {
  // can be audio or video track, if tile with only audio track is pinned
  const aspectRatio = useWindowSize();
  const pinnedTrack = usePinnedTrack();
  const peerVideoTrack = useHMSStore(
    selectVideoTrackByPeerID(pinnedTrack.peerId)
  );
  const pinnedVideoTrack =
    pinnedTrack && pinnedTrack.type === 'audio' ? peerVideoTrack : pinnedTrack;
  const [ref, { height, width }] = useMeasure();
  const peers = (useHMSStore(selectPeers) || []).filter(
    (peer) =>
      peer.videoTrack || peer.audioTrack || peer.auxiliaryTracks.length > 0
  );
  if (peers.length === 0) {
    return null;
  }
  const showSidePane = pinnedTrack && peers.length > 1;

  let finalWidth = (aspectRatio.width / aspectRatio.height) * height;
  let finalHeight = height;

  if (finalWidth > width) {
    finalWidth = width;
    finalHeight = (aspectRatio.height / aspectRatio.width) * width;
  }

  return (
    <StyledContainer style={{ height: '100%', width: '100%' }}>
      <StyledContainer
        style={{
          flex: '1 1 0',
          padding: 32,
          minHeight: 0,
          minWidth: 0,
          justifyContent: 'center',
          alignItems: 'center',
        }}
        ref={ref}
      >
        <VideoTile
          key={pinnedTrack.id}
          trackId={pinnedVideoTrack?.id}
          peerId={pinnedTrack.peerId}
          height={finalHeight}
          width={finalWidth}
        />
      </StyledContainer>
      {showSidePane && (
        <GridSidePaneView
          peers={peers.filter((peer) => peer.id !== pinnedTrack.peerId)}
        />
      )}
    </StyledContainer>
  );
};

export default PinnedPeerView;
