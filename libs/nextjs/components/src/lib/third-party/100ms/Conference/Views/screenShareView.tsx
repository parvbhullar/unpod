import React, {Fragment, useCallback, useMemo} from 'react';
import {
  selectLocalPeerID,
  selectLocalPeerRoleName,
  selectPeers,
  selectPeerScreenSharing,
  selectPeerSharingVideoPlaylist,
  selectScreenShareByPeerID,
  useHMSStore,
} from '@100mslive/react-sdk';
import {ScreenshareDisplay} from './ScreenshareDisplay';
import ScreenshareTile from './ScreenshareTile';
import VideoList from './VideoList';
import VideoTile from './VideoTile';
import {VideoPlayer} from './Playlist/VideoPlayer';

const ScreenShareView = () => {
  const showSidebarInBottom = true;
  const peers = useHMSStore(selectPeers);
  const localPeerID = useHMSStore(selectLocalPeerID);
  const localPeerRole = useHMSStore(selectLocalPeerRoleName);
  const peerPresenting = useHMSStore(selectPeerScreenSharing);
  const peerSharingPlaylist = useHMSStore(selectPeerSharingVideoPlaylist);
  const isPresenterFromMyRole =
    peerPresenting?.roleName?.toLowerCase() === localPeerRole?.toLowerCase();
  const amIPresenting = localPeerID === peerPresenting?.id;
  const showPresenterInSmallTile =
    showSidebarInBottom || amIPresenting || isPresenterFromMyRole;

  const smallTilePeers = useMemo(() => {
    const smallTilePeers = peers.filter(
      (peer) => peer.id !== peerPresenting?.id
    );
    if (showPresenterInSmallTile && peerPresenting) {
      smallTilePeers.unshift(peerPresenting); // put presenter on first page
    }
    return smallTilePeers;
  }, [peers, peerPresenting, showPresenterInSmallTile]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: showSidebarInBottom ? 'column' : 'row',
        size: '100%',
      }}
    >
      <ScreenShareComponent
        amIPresenting={amIPresenting}
        peerPresenting={peerPresenting}
        peerSharingPlaylist={peerSharingPlaylist}
      />
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          padding: '1rem 2rem',
          flex: '0 0 20%',
        }}
      >
        <SidePane
          showSidebarInBottom={showSidebarInBottom}
          peerScreenSharing={peerPresenting}
          isPresenterInSmallTiles={showPresenterInSmallTile}
          smallTilePeers={smallTilePeers}
          totalPeers={peers.length}
        />
      </div>
    </div>
  );
};

// Sidepane will show the camera stream of the main peer who is screensharing
// and both camera + screen(if applicable) of others
export const SidePane = ({
                           isPresenterInSmallTiles,
                           peerScreenSharing, // the peer who is screensharing
                           smallTilePeers,
                           totalPeers,
                           showSidebarInBottom,
                         }) => {
  // The main peer's screenshare is already being shown in center view
  const shouldShowScreenFn = useCallback(
    (peer) => peerScreenSharing && peer.id !== peerScreenSharing.id,
    [peerScreenSharing]
  );
  return (
    <Fragment>
      {!isPresenterInSmallTiles && (
        <LargeTilePeerView peerScreenSharing={peerScreenSharing}/>
      )}
      <SmallTilePeersView
        showSidebarInBottom={showSidebarInBottom}
        smallTilePeers={smallTilePeers}
        shouldShowScreenFn={shouldShowScreenFn}
      />
    </Fragment>
  );
};

const ScreenShareComponent = ({
                                amIPresenting,
                                peerPresenting,
                                peerSharingPlaylist,
                              }) => {
  const screenshareTrack = useHMSStore(
    selectScreenShareByPeerID(peerPresenting?.id)
  );

  if (peerSharingPlaylist) {
    return (
      <div
        style={{
          mx: '$8',
          flex: '3 1 0',
          '@xl': {
            flex: '2 1 0',
            display: 'flex',
            alignItems: 'center',
          },
        }}
      >
        <VideoPlayer peerId={peerSharingPlaylist.id}/>
      </div>
    );
  }

  return (
    <div
      style={{
        flex: '3 1 0',
        marginLeft: 16,
        marginRight: 16,
      }}
    >
      {peerPresenting &&
        (amIPresenting &&
        !['browser', 'window', 'application'].includes(
          screenshareTrack?.displaySurface
        ) ? (
          <div style={{objectFit: 'contain', h: '100%'}}>
            <ScreenshareDisplay/>
          </div>
        ) : (
          <ScreenshareTile peerId={peerPresenting?.id}/>
        ))}
    </div>
  );
};

const SmallTilePeersView = ({
                              smallTilePeers,
                              shouldShowScreenFn,
                              showStatsOnTiles,
                              showSidebarInBottom,
                            }) => {
  return (
    <div
      style={{
        display: 'flex',
        flex: '2 1 0',
      }}
    >
      {smallTilePeers && smallTilePeers.length > 0 && (
        <VideoList
          peers={smallTilePeers}
          maxColCount={showSidebarInBottom ? undefined : 1}
          maxRowCount={showSidebarInBottom ? 1 : undefined}
          includeScreenShareForPeer={shouldShowScreenFn}
        />
      )}
    </div>
  );
};

const LargeTilePeerView = ({peerScreenSharing, showStatsOnTiles}) => {
  return peerScreenSharing ? (
    <div
      style={{
        flex: '1 1 0',
        minHeight: '25%',
        paddingLeft: 12,
        paddingRight: 12,
      }}
    >
      <VideoTile
        showStatsOnTiles={showStatsOnTiles}
        width="100%"
        height="100%"
        peerId={peerScreenSharing.id}
      />
    </div>
  ) : null;
};

export default ScreenShareView;
