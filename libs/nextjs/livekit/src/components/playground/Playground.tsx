'use client';
import '@livekit/components-styles';
import { LoadingSVG } from '../button/LoadingSVG';
import { AudioInputTile } from '../config/AudioInputTile';
import { ConfigurationPanelItem } from '../config/ConfigurationPanelItem';
import { useConfig } from '../../hooks/useConfig';
import { TranscriptionTile } from '../../transcriptions/TranscriptionTile';
import {
  BarVisualizer,
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useDataChannel,
  useLocalParticipant,
  useRemoteParticipants,
  useRoomContext,
  useTracks,
  useVoiceAssistant,
} from '@livekit/components-react';
import { ConnectionState, LocalParticipant, Track } from 'livekit-client';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AudioTileContainer,
  Container,
  FlexColumnCenter,
  StyledAgentContainer,
  StyledPlaygroundTile,
  StyledVisualizerContainer,
} from './Playground.styled';
import { Button, Col } from 'antd';

type PlaygroundProps = {
  onConnect: (shouldConnect: boolean) => void;};

const Playground: React.FC<PlaygroundProps> = ({ onConnect }) => {
  const { config } = useConfig();
  const [, setTranscripts] = useState<
    {
      name: string;
      message: string;
      timestamp: number;
      isSelf: boolean;
    }[]
  >([]);
  const { localParticipant } = useLocalParticipant();
  const remoteParticipants = useRemoteParticipants();
  const voiceAssistant = useVoiceAssistant();
  console.log('voiceAssistant:', voiceAssistant);
  console.log('remoteParticipants:', remoteParticipants);
  const roomState = useConnectionState();
  const tracks = useTracks();
  const room = useRoomContext();

  useEffect(() => {
    if (roomState === ConnectionState.Connected) {
      localParticipant.setMicrophoneEnabled(config.settings.inputs.mic);
      room.activeSpeakers.map((participant) => {
        console.log('activeSpeakers', participant);
        participant.audioLevel = 1;
      });
    }
  }, [config, localParticipant, roomState]);

  const localTracks = tracks.filter(
    ({ participant }) => participant instanceof LocalParticipant,
  );
  const localMicTrack = localTracks.find(
    ({ source }) => source === Track.Source.Microphone,
  );

  const onDataReceived = useCallback(
    (msg: { topic?: string; payload: Uint8Array }) => {
      if (msg.topic === 'transcription') {
        const decoded = JSON.parse(
          new TextDecoder('utf-8').decode(msg.payload),
        ) as { text?: string; timestamp?: number };
        let timestamp = new Date().getTime();
        if (decoded.timestamp && decoded.timestamp > 0) {
          timestamp = decoded.timestamp;
        }
        setTranscripts((prev) => [
          ...prev,
          {
            name: 'You',
            message: decoded.text || '',
            timestamp,
            isSelf: true,
          },
        ]);
      }
    },
    [],
  );

  useDataChannel('transcription', onDataReceived);

  const audioTileContent = useMemo(() => {
    const disconnectedContent = (
      <FlexColumnCenter>
        No audio track. Connect to get started.
        <Button color="primary" variant="solid" onClick={() => onConnect(true)}>
          Connect
        </Button>
      </FlexColumnCenter>
    );

    const waitingContent = (
      <FlexColumnCenter>
        <LoadingSVG />
        Waiting for audio track
      </FlexColumnCenter>
    );

    const visualizerContent = (
      <BarVisualizer
        state={voiceAssistant.state}
        trackRef={voiceAssistant.audioTrack}
        options={{ minHeight: 80, maxHeight: 100 }}
      />
    );

    if (roomState === ConnectionState.Disconnected) {
      return disconnectedContent;
    }

    if (!voiceAssistant.audioTrack) {
      return waitingContent;
    }

    return visualizerContent;
  }, [roomState, voiceAssistant]);

  const chatTileContent = useMemo(() => {
    if (voiceAssistant.audioTrack) {
      return <TranscriptionTile agentAudioTrack={voiceAssistant.audioTrack} />;
    }
    return <></>;
  }, [voiceAssistant.audioTrack]);

  console.log('roomState:', voiceAssistant.state, ConnectionState.Connected);
  return (
    <>
      <Container>
        <Col span={12}>
          {config.settings.chat &&
            voiceAssistant.state !== ConnectionState.Connecting &&
            voiceAssistant.state !== ConnectionState.Disconnected && (
              <StyledPlaygroundTile title="Chat">
                {chatTileContent}
              </StyledPlaygroundTile>
            )}
        </Col>

        <Col span={12}>
          <StyledAgentContainer $direction="row">
            {config.settings.outputs.audio && (
              <StyledVisualizerContainer>
                <AudioTileContainer>{audioTileContent}</AudioTileContainer>
              </StyledVisualizerContainer>
            )}
            {roomState === ConnectionState.Connected && (
              <ConfigurationPanelItem
                roomState={roomState}
                onConnectClicked={() => onConnect(false)}
              >
                {localMicTrack && <AudioInputTile trackRef={localMicTrack} />}
              </ConfigurationPanelItem>
            )}
          </StyledAgentContainer>
        </Col>
      </Container>

      {roomState === ConnectionState.Connected && (
        <>
          <RoomAudioRenderer />
          <StartAudio label="Click to enable audio playback" />
        </>
      )}
    </>
  );
};

export default Playground;
