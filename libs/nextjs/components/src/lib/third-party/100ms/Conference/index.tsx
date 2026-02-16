import React, { useEffect, useRef, useState } from 'react';
import {
  selectAppData,
  selectIsConnectedToRoom,
  selectRoomState,
  useHMSActions,
  useHMSStore,
} from '@100mslive/react-sdk';
import { ConferenceMainView } from './Views/mainView';
import Footer from './Footer';
import SideBar from './SideBar';
import FullPageProgress from '../../../common/AppLoader';
import { RoleChangeRequestModal } from './RoleChangeRequestModal';
import { useIsHeadless } from '../AppData/useUISettings';
import {
  APP_DATA,
  EMOJI_REACTION_TYPE,
  isAndroid,
  isIOS,
  isIPadOS,
} from '../common/constants';
import {
  StyledContainer,
  StyledFooterContainer,
  StyledRoot,
} from './index.styled';
import { useRouter } from 'next/navigation';
import { useMediaQuery } from 'react-responsive';
import { TabWidthQuery } from '@unpod/constants';

const Conference = () => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const router = useRouter();
  const isHeadless = useIsHeadless();
  const roomState = useHMSStore(selectRoomState);
  const isConnectedToRoom = useHMSStore(selectIsConnectedToRoom);
  const hmsActions = useHMSActions();
  const [hideControls, setHideControls] = useState(false);
  const dropdownList = useHMSStore(selectAppData(APP_DATA.dropdownList));
  const footerRef = useRef();
  const dropdownListRef = useRef();
  const performAutoHide = hideControls && (isAndroid || isIOS || isIPadOS);

  const toggleControls = (e) => {
    if (dropdownListRef.current?.length === 0) {
      setHideControls((value) => !value);
    }
  };

  useEffect(() => {
    let timeout = null;
    dropdownListRef.current = dropdownList || [];
    if (dropdownListRef.current.length === 0) {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        if (dropdownListRef.current.length === 0) {
          setHideControls(true);
        }
      }, 5000);
    }
    return () => {
      clearTimeout(timeout);
    };
  }, [dropdownList, hideControls]);

  // useEffect(() => {
  //   if (!roomId) {
  //     router.back();
  //     return;
  //   }
  //   if (
  //     !prevState &&
  //     !(
  //       roomState === HMSRoomState.Connecting ||
  //       roomState === HMSRoomState.Reconnecting ||
  //       isConnectedToRoom
  //     )
  //   ) {
  //     if (role) router.push(`/preview/${roomId || ''}/${role}`);
  //     else router.push(`/preview/${roomId || ''}`);
  //   }
  // }, [isConnectedToRoom, prevState, roomState, role, roomId]);

  useEffect(() => {
    // beam doesn't need to store messages, saves on unnecessary store updates in large calls
    if (isHeadless) {
      hmsActions.ignoreMessageTypes(['chat', EMOJI_REACTION_TYPE]);
    }
  }, [isHeadless, hmsActions]);

  if (!isConnectedToRoom) {
    return <FullPageProgress />;
  }

  return (
    <StyledRoot>
      <StyledContainer style={{ flex: isTabletOrMobile ? 1 : 2 }}>
        <div
          style={{
            width: '100%',
            // flex: '1 1 0',
            minHeight: 0,
            height: 'calc(100% - 70px)',
            paddingBottom: 'env(safe-area-inset-bottom)',
          }}
          id="conferencing"
          data-testid="conferencing"
          onClick={toggleControls}
        >
          <ConferenceMainView />
        </div>
        {!isHeadless && (
          <StyledFooterContainer
            ref={footerRef}
            style={{
              flexShrink: 0,
              maxHeight: 48,
              transition: 'margin 0.3s ease-in-out',
              marginBottom: performAutoHide
                ? `-${footerRef.current?.clientHeight}px`
                : undefined,
            }}
            /*style={{
            flexShrink: 0,
            maxHeight: 48,
            transition: 'margin 0.3s ease-in-out',
            marginBottom: performAutoHide
              ? `-${footerRef.current?.clientHeight}px`
              : undefined,
          }}*/
            data-testid="footer"
          >
            <Footer />
          </StyledFooterContainer>
        )}
      </StyledContainer>

      <SideBar />
      <RoleChangeRequestModal />
    </StyledRoot>
  );
};

export default Conference;
