'use client';
import '@livekit/components-styles';
import { ConfigurationPanelItem } from '@unpod/livekit/components/config/ConfigurationPanelItem';
import {
  BarVisualizer,
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useLocalParticipant,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';
import React, { useEffect } from 'react';
import {
  StyledAgentContainer,
  StyledVisualizerContainer,
} from '@unpod/livekit/components/playground/Playground.styled';
import styled from 'styled-components';

export const AudioTileContainer = styled.div`
  display: flex;
  height: 60px;
  color: #333333;
  width: 100%;
`;
type CallViewProps = {
  onConnect: (shouldConnect: boolean) => void;
};

const CallView: React.FC<CallViewProps> = ({ onConnect }) => {
  const { localParticipant } = useLocalParticipant();
  const voiceAssistant = useVoiceAssistant();
  const roomState = useConnectionState();
  const room = useRoomContext();

  useEffect(() => {
    if (roomState === ConnectionState.Connected) {
      localParticipant.setMicrophoneEnabled(true);
      room.activeSpeakers.map((participant) => {
        console.log('activeSpeakers', participant);
        participant.audioLevel = 1;
      });
    }
  }, [localParticipant, roomState]);

  return (
    <>
      <StyledAgentContainer $direction="row">
        <StyledVisualizerContainer>
          <AudioTileContainer>
            <BarVisualizer
              state={voiceAssistant.state}
              barCount={12}
              trackRef={voiceAssistant.audioTrack}
              options={{ minHeight: 50, maxHeight: 100 }}
            />
          </AudioTileContainer>
        </StyledVisualizerContainer>
        {roomState === ConnectionState.Connected && (
          <ConfigurationPanelItem
            roomState={roomState}
            onConnectClicked={() => onConnect(false)}
          />
        )}
      </StyledAgentContainer>

      {roomState === ConnectionState.Connected && (
        <>
          <RoomAudioRenderer />
          <StartAudio label="Click to enable audio playback" />
        </>
      )}
    </>
  );
};

export default CallView;
