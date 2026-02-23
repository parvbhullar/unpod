import React from 'react';
import {AudioVideoToggle} from './AudioVideoToggle';
import {LeaveRoom} from './LeaveRoom';
import MetaActions from './MetaActions';
// import { PIP } from '../PIP';
import {ScreenshareToggle} from './ScreenShare';
import {Button, Space, Tooltip} from 'antd';
import {selectIsAllowedToPublish, useHMSActions, useHMSStore, useScreenShare,} from '@100mslive/react-sdk';
import {useIsFeatureEnabled} from '../../hooks/useFeatures';
import {FEATURE_LIST} from '../../common/constants';
import {isScreenshareSupported} from '../../common/utils';
import {IoIosMusicalNotes} from 'react-icons/io';
import {ToggleWhiteboard} from '../../plugin/whiteboard';
import {StartRecording} from '../StreamActions';
import {VirtualBackground} from '../../plugin/VirtualBackground/VirtualBackground';

const ScreenshareAudio = () => {
  const {
    amIScreenSharing,
    screenShareVideoTrackId: video,
    screenShareAudioTrackId: audio,
    toggleScreenShare,
  } = useScreenShare();
  const isAllowedToPublish = useHMSStore(selectIsAllowedToPublish);
  const isAudioScreenshare = amIScreenSharing && !video && !!audio;
  const hmsActions = useHMSActions();
  const isFeatureEnabled = useIsFeatureEnabled(
    FEATURE_LIST.AUDIO_ONLY_SCREENSHARE
  );
  if (
    !isFeatureEnabled ||
    !isAllowedToPublish.screen ||
    !isScreenshareSupported()
  ) {
    return null;
  }
  return (
    <Tooltip
      title={`${!isAudioScreenshare ? 'Start' : 'Stop'} audio sharing`}
      key="shareAudio"
    >
      <Button
        type={isAudioScreenshare ? 'primary' : 'default'}
        shape="circle"
        onClick={() => {
          if (amIScreenSharing) {
            toggleScreenShare();
          } else {
            hmsActions
              .setScreenShareEnabled(true, {
                audioOnly: true,
                displaySurface: 'browser',
              })
              .catch(console.error);
          }
        }}
        data-testid="screenshare_audio"
      >
        <IoIosMusicalNotes fontSize={20}/>
      </Button>
    </Tooltip>
  );
};
export const ConferencingFooter = () => {
  const isMobile = false;
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <Space>
        <ScreenshareAudio/>
        <ToggleWhiteboard/>
        <StartRecording/>
        <VirtualBackground/>
        {/*{FeatureFlags.enableWhiteboard ? <ToggleWhiteboard /> : null}*/}
      </Space>
      <Space>
        <AudioVideoToggle/>
        <ScreenshareToggle/>
        <LeaveRoom/>
      </Space>

      <MetaActions/>
    </div>
  );
};
