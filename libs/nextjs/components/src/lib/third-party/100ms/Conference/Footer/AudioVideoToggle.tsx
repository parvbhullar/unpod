import React, {useEffect} from 'react';
import {
  selectIsConnectedToRoom,
  selectLocalVideoTrackID,
  selectVideoTrackByID,
  useAVToggle,
  useHMSActions,
  useHMSStore,
  useParticipants,
} from '@100mslive/react-sdk';
import {MdCameraswitch, MdMic, MdMicOff, MdVideocam, MdVideocamOff,} from 'react-icons/md';

import {isMacOS} from '../../common/constants';
import {Button, Space, Tooltip} from 'antd';
import {useInfoViewActionsContext} from '@unpod/providers';

export const AudioVideoToggle = () => {
  const {isLocalVideoEnabled, isLocalAudioEnabled, toggleAudio, toggleVideo} =
    useAVToggle();
  const actions = useHMSActions();
  const videoTracKId = useHMSStore(selectLocalVideoTrackID);
  const localVideoTrack = useHMSStore(selectVideoTrackByID(videoTracKId));
  const isConnectedToRoom = useHMSStore(selectIsConnectedToRoom);
  const infoViewActionsContext = useInfoViewActionsContext();

  const {participants} = useParticipants();
  const isHost =
    participants.find((p) => p.videoTrack === localVideoTrack?.id)?.roleName ===
    'host';

  useEffect(() => {
    if (!isHost) {
      if (isLocalAudioEnabled) toggleAudio();
      if (isLocalVideoEnabled) toggleVideo();
    }
  }, [isHost]);

  return (
    <Space direction="horizontal">
      {toggleAudio ? (
        <Tooltip
          title={`Turn ${isLocalAudioEnabled ? 'off' : 'on'} audio (${
            isMacOS ? '⌘' : 'ctrl'
          } + m)`}
        >
          <Button
            onClick={toggleAudio}
            key="toggleAudio"
            disabled={!isHost}
            data-testid="audio_btn"
            type={isLocalAudioEnabled ? 'primary' : 'default'}
            shape="circle"
            icon={
              !isLocalAudioEnabled ? (
                <MdMicOff data-testid="audio_off_btn" fontSize={20}/>
              ) : (
                <MdMic data-testid="audio_on_btn" fontSize={20}/>
              )
            }
          />
        </Tooltip>
      ) : null}
      {toggleVideo ? (
        <Tooltip
          title={`Turn ${isLocalVideoEnabled ? 'off' : 'on'} video (${
            isMacOS ? '⌘' : 'ctrl'
          } + e)`}
        >
          <Button
            key="toggleVideo"
            active={isLocalVideoEnabled}
            onClick={toggleVideo}
            type={isLocalVideoEnabled ? 'primary' : 'default'}
            shape="circle"
            disabled={!isHost}
            icon={
              !isLocalVideoEnabled ? (
                <MdVideocamOff data-testid="video_off_btn" fontSize={20}/>
              ) : (
                <MdVideocam data-testid="video_on_btn" fontSize={20}/>
              )
            }
            data-testid="video_btn"
          />
        </Tooltip>
      ) : null}
      {localVideoTrack?.facingMode && isConnectedToRoom ? (
        <Tooltip title="Switch Camera" key="switchCamera">
          <Button
            shape="circle"
            disabled={!isHost}
            onClick={async () => {
              try {
                await actions.switchCamera();
              } catch (e) {
                infoViewActionsContext.showError(
                  `Error while flipping camera ${e.message || ''}`,
                );
              }
            }}
            icon={<MdCameraswitch fontSize={20}/>}
          />
        </Tooltip>
      ) : null}
    </Space>
  );
};
