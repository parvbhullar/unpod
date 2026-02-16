'use client';
import '@livekit/components-styles';
import { ConfigurationPanelItem } from '@unpod/livekit/components/config/ConfigurationPanelItem';
import {
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useDataChannel,
  useLocalParticipant,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';
import { useCallback, useEffect, useState } from 'react';
import {
  StyledAgentContainer,
  StyledVisualizerContainer,
} from '@unpod/livekit/components/playground/Playground.styled';
import AudioOutputTile from '@unpod/livekit/components/config/AudioOutputTile';
import { useIntl } from 'react-intl';

type TranscriptItem = {
  name: string;
  message: any;
  timestamp: number;
  isSelf: boolean;
};

type VoiceAgentProps = {
  onConnect: (connected: boolean) => void;
  spaceView?: boolean;
};

const VoiceAgent = ({ onConnect, spaceView }: VoiceAgentProps) => {
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([]);
  const { localParticipant } = useLocalParticipant();
  const voiceAssistant = useVoiceAssistant();
  const roomState = useConnectionState();
  const room = useRoomContext();
  const { formatMessage } = useIntl();

  useEffect(() => {
    if (roomState !== ConnectionState.Connected) {
      return;
    }

    localParticipant.setMicrophoneEnabled(true);
    room.activeSpeakers.map((participant) => {
      console.log('activeSpeakers', participant);
      participant.audioLevel = 1;
    });

    return () => {
      if (localParticipant) {
        console.log('🎤 Stopping and unpublishing microphone on cleanup');

        // First disable the microphone
        localParticipant.setMicrophoneEnabled(false);

        // Then unpublish all audio tracks to release browser permission
        localParticipant.audioTrackPublications.forEach((publication) => {
          if (publication.track) {
            publication.track.stop();
            localParticipant.unpublishTrack(publication.track);
          }
        });
      }
    };
  }, [localParticipant, roomState, room]);

  const onDataReceived = useCallback(
    (msg: any) => {
      console.log('msg', msg);
      // if (msg.topic === 'transcription'|| msg.topic === 'transcription') {
      const decoded = JSON.parse(new TextDecoder('utf-8').decode(msg.payload));
      let timestamp = new Date().getTime();
      if ('timestamp' in decoded && decoded.timestamp > 0) {
        timestamp = decoded.timestamp;
      }
      console.log('transcription**', decoded, decoded.data.data);
      setTranscripts((prev) => [
        ...prev,
        {
          name: 'You',
          message: decoded.text,
          timestamp: timestamp,
          isSelf: true,
        },
      ]);
      // }
    },
    [transcripts],
  );

  useDataChannel(onDataReceived);
  return (
    <>
      <StyledAgentContainer
        // $direction={config?.circular ? 'row' : 'column'}
        $direction="row"
        $spaceView={spaceView}
      >
        <StyledVisualizerContainer $spaceView={spaceView}>
          <AudioOutputTile
            state={voiceAssistant.state}
            trackRef={voiceAssistant.audioTrack}
            spaceView={spaceView}
          />
        </StyledVisualizerContainer>

        {roomState === ConnectionState.Connected && (
          <ConfigurationPanelItem
            roomState={roomState}
            onConnectClicked={() => onConnect(false)}
            spaceView={spaceView}
          >
            {/* {localMicTrack && (
              <AudioInputTile config={config} trackRef={localMicTrack} />
            )}*/}
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
