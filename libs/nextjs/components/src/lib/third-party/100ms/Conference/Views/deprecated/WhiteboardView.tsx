import React from 'react';
import { selectPeers, selectRoomID, useHMSStore } from '@100mslive/react-sdk';
import { SidePane } from '../screenShareView';
import { Whiteboard } from '../../../plugin/whiteboard';

const Editor = React.memo(({ roomId }) => {
  return (
    <div
      style={{
        mx: '$4',
        flex: '3 1 0',
        '@lg': {
          flex: '2 1 0',
          '& video': {
            objectFit: 'contain',
          },
        },
      }}
    >
      <div style={{ position: 'relative', width: '100%', height: '100%' }}>
        <Whiteboard roomId={roomId} />
      </div>
    </div>
  );
});

const WhiteboardView = () => {
  // for smaller screen we will show sidebar in bottom
  const showSidebarInBottom = true;
  const peers = useHMSStore(selectPeers);
  const roomId = useHMSStore(selectRoomID);
  return (
    <div style={{ display: 'flex', width: '100%', height: '100%' }}>
      <Editor roomId={roomId} />
      <div
        style={{
          display: 'flex',
          overflow: 'hidden',
          padding: 16,
          flex: '0 0 20%',
        }}
      >
        <SidePane
          showSidebarInBottom={showSidebarInBottom}
          isPresenterInSmallTiles={true}
          smallTilePeers={peers}
          totalPeers={peers.length}
        />
      </div>
    </div>
  );
};

export default WhiteboardView;
