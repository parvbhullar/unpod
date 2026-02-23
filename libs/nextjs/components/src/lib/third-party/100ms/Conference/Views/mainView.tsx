import React, {Suspense, useEffect} from 'react';
import {
  selectIsConnectedToRoom,
  selectLocalPeerRoleName,
  selectPeerScreenSharing,
  selectPeerSharingAudio,
  selectPeerSharingVideoPlaylist,
  selectTemplateAppData,
  useHMSActions,
  useHMSStore,
} from '@100mslive/react-sdk';
import FullPageProgress from '../../../../common/AppLoader';
import EmbedView from './EmbedView';
import InsetView from './InsetView';
import MainGridView from './MainGridView';
import PDFView from './PDFView';
import ScreenShareView from './screenShareView';
import WaitingView from './WaitingView';
import {useAppConfig} from '../../AppData/useAppConfig';
import {
  useHLSViewerRole,
  useIsHeadless,
  usePDFAnnotator,
  usePinnedTrack,
  useUISettings,
  useUrlToEmbed,
  useWaitingViewerRole,
} from '../../AppData/useUISettings';
import {SESSION_STORE_KEY, UI_MODE_ACTIVE_SPEAKER,} from '../../common/constants';
import {StyledContainer} from './index.styled';
import {useWhiteboardMetadata} from '../../plugin/whiteboard';

const WhiteboardView = React.lazy(() => import('./WhiteBoardView'));
const HLSView = React.lazy(() => import('./HLSView'));
const ActiveSpeakerView = React.lazy(() => import('./ActiveSpeakerView'));
const PinnedTrackView = React.lazy(() => import('./PinnedTrackView'));

export const ConferenceMainView = () => {
  const localPeerRole = useHMSStore(selectLocalPeerRoleName);
  const pinnedTrack = usePinnedTrack();
  const peerSharing = useHMSStore(selectPeerScreenSharing);
  const peerSharingAudio = useHMSStore(selectPeerSharingAudio);
  const peerSharingPlaylist = useHMSStore(selectPeerSharingVideoPlaylist);
  const {whiteboardOwner: whiteboardShared} = useWhiteboardMetadata();
  const isConnected = useHMSStore(selectIsConnectedToRoom);
  const uiMode = useHMSStore(selectTemplateAppData).uiMode;
  const hmsActions = useHMSActions();
  const isHeadless = useIsHeadless();
  const headlessUIMode = useAppConfig('headlessConfig', 'uiMode');
  const {uiViewMode, isAudioOnly} = useUISettings();
  const hlsViewerRole = useHLSViewerRole();
  const waitingViewerRole = useWaitingViewerRole();
  const urlToIframe = useUrlToEmbed();
  const pdfAnntatorActive = usePDFAnnotator();
  useEffect(() => {
    if (!isConnected) {
      return;
    }
    const audioPlaylist = JSON.parse(
      process.env.REACT_APP_AUDIO_PLAYLIST || '[]'
    );
    const videoPlaylist = JSON.parse(
      process.env.REACT_APP_VIDEO_PLAYLIST || '[]'
    );
    if (videoPlaylist.length > 0) {
      hmsActions.videoPlaylist.setList(videoPlaylist);
    }
    if (audioPlaylist.length > 0) {
      hmsActions.audioPlaylist.setList(audioPlaylist);
    }

    hmsActions.sessionStore.observe([
      SESSION_STORE_KEY.PINNED_MESSAGE,
      SESSION_STORE_KEY.SPOTLIGHT,
    ]);
  }, [isConnected, hmsActions]);

  if (!localPeerRole) {
    // we don't know the role yet to decide how to render UI
    return null;
  }

  console.log(
    'localPeerRole',
    localPeerRole,
    hlsViewerRole,
    isHeadless,
    uiViewMode,
    UI_MODE_ACTIVE_SPEAKER
  );

  let ViewComponent;
  if (localPeerRole === hlsViewerRole) {
    console.log('ViewComponent', 'HLSView');
    ViewComponent = HLSView;
  } else if (localPeerRole === waitingViewerRole) {
    console.log('ViewComponent', 'WaitingView');
    ViewComponent = WaitingView;
  } else if (pdfAnntatorActive) {
    console.log('ViewComponent', 'PDFView');
    ViewComponent = PDFView;
  } else if (urlToIframe) {
    console.log('ViewComponent', 'EmbedView');
    ViewComponent = EmbedView;
  } else if (whiteboardShared) {
    ViewComponent = WhiteboardView;
  } else if (uiMode === 'inset') {
    console.log('ViewComponent', 'InsetView');
    ViewComponent = InsetView;
  } else if (
    ((peerSharing && peerSharing.id !== peerSharingAudio?.id) ||
      peerSharingPlaylist) &&
    !isAudioOnly
  ) {
    console.log('ViewComponent', 'ScreenShareView');
    ViewComponent = ScreenShareView;
  } else if (pinnedTrack) {
    console.log('ViewComponent', 'PinnedTrackView');
    ViewComponent = PinnedTrackView;
  } else if (
    uiViewMode === UI_MODE_ACTIVE_SPEAKER ||
    (isHeadless && headlessUIMode === UI_MODE_ACTIVE_SPEAKER)
  ) {
    console.log('ViewComponent', 'ActiveSpeakerView');
    ViewComponent = ActiveSpeakerView;
  } else {
    console.log('ViewComponent', 'MainGridView');
    ViewComponent = MainGridView;
  }

  return (
    <Suspense fallback={<FullPageProgress/>}>
      <StyledContainer
        style={{
          height: '100%',
          width: '100%',
          position: 'relative',
        }}
      >
        <ViewComponent/>
      </StyledContainer>
    </Suspense>
  );
};
