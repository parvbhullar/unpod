import React from 'react';
import {selectPeers, selectRoomID, useHMSStore} from '@100mslive/react-sdk';
import {SidePane} from '../screenShareView';
import {Whiteboard} from '../../../plugin/whiteboard';
import {StyledContainer, StyledEditorContainer, StyledEditorRoot, StyledSidePaneContainer,} from './index.styled';
import {useMediaQuery} from 'react-responsive';
import {DesktopWidthQuery} from '@unpod/constants';

const Editor = React.memo(({roomId}) => {
  return (
    <StyledEditorRoot>
      <StyledEditorContainer>
        <Whiteboard roomId={roomId}/>
      </StyledEditorContainer>
    </StyledEditorRoot>
  );
});

const WhiteBoardView = () => {
  // for smaller screen we will show sidebar in bottom
  const showSidebarInBottom = useMediaQuery(DesktopWidthQuery);
  const peers = useHMSStore(selectPeers);
  const roomId = useHMSStore(selectRoomID);
  return (
    <StyledContainer
      style={{flexDirection: showSidebarInBottom ? 'column' : 'row'}}
    >
      <Editor roomId={roomId}/>
      <StyledSidePaneContainer>
        <SidePane
          showSidebarInBottom={showSidebarInBottom}
          isPresenterInSmallTiles={true}
          smallTilePeers={peers}
          totalPeers={peers.length}
        />
      </StyledSidePaneContainer>
    </StyledContainer>
  );
};

export default WhiteBoardView;
