'use client';
import '@livekit/components-styles';
import { AudioInputTile } from '@unpod/livekit/components/config/AudioInputTile';
import { ConfigurationPanelItem } from '@unpod/livekit/components/config/ConfigurationPanelItem';
import {
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useDataChannel,
  useLocalParticipant,
  useRoomContext,
  useTracks,
  useVoiceAssistant,
} from '@livekit/components-react';
import { ConnectionState, LocalParticipant, Track } from 'livekit-client';
import React, { useCallback, useEffect, useState } from 'react';
import {
  StyledAgentContainer,
  StyledVisualizerContainer,
} from '@unpod/livekit/components/playground/Playground.styled';
import AudioOutputTile from '@unpod/livekit/components/config/AudioOutputTile';
import { useKrispNoiseFilter } from '@livekit/components-react/krisp';
import { useIntl } from 'react-intl';

const VoiceAgent = ({ onConnect, config }) => {
  const [transcripts, setTranscripts] = useState([]);
  const { localParticipant } = useLocalParticipant();
  const voiceAssistant = useVoiceAssistant();
  const roomState = useConnectionState();
  const tracks = useTracks();
  const room = useRoomContext();
  const { formatMessage } = useIntl();

  const krisp = useKrispNoiseFilter();

  useEffect(() => {
    if (roomState === ConnectionState.Connected) {
      krisp.setNoiseFilterEnabled(true);
      localParticipant.setMicrophoneEnabled(true);
      room.activeSpeakers.map((participant) => {
        console.log('activeSpeakers', participant);
        participant.audioLevel = 1;
      });
    }
  }, [localParticipant, roomState]);

  const localTracks = tracks.filter(
    ({ participant }) => participant instanceof LocalParticipant,
  );
  const localMicTrack = localTracks.find(
    ({ source }) => source === Track.Source.Microphone,
  );

  const onDataReceived = useCallback(
    (msg) => {
      console.log('msg', msg);
      if (msg.topic === 'transcription') {
        const decoded = JSON.parse(
          new TextDecoder('utf-8').decode(msg.payload),
        );
        let timestamp = new Date().getTime();
        if ('timestamp' in decoded && decoded.timestamp > 0) {
          timestamp = decoded.timestamp;
        }
        setTranscripts([
          ...transcripts,
          {
            name: 'You',
            message: decoded.text,
            timestamp: timestamp,
            isSelf: true,
          },
        ]);
      }
    },
    [transcripts],
  );

  useDataChannel(onDataReceived);
  return (
    <>
      <StyledAgentContainer direction={config?.circular ? 'row' : 'column'}>
        <StyledVisualizerContainer>
          <AudioOutputTile
            config={config}
            state={voiceAssistant.state}
            trackRef={voiceAssistant.audioTrack}
          />
        </StyledVisualizerContainer>
        {roomState === ConnectionState.Connected && (
          <ConfigurationPanelItem
            roomState={roomState}
            onConnectClicked={() =>
              onConnect(roomState === ConnectionState.Disconnected)
            }
          >
            {localMicTrack && (
              <AudioInputTile config={config} trackRef={localMicTrack} />
            )}
          </ConfigurationPanelItem>
        )}
      </StyledAgentContainer>

      {roomState === ConnectionState.Connected && (
        <>
          <RoomAudioRenderer />
          <StartAudio
            label={formatMessage({ id: 'talkToAgent.playbackMessage' })}
          />
        </>
      )}
    </>
  );
};

export default VoiceAgent;
