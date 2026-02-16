import '@livekit/components-styles';
import { ConfigurationPanelItem } from './config/ConfigurationPanelItem';
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
import { ConnectionState, Track } from 'livekit-client';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import AudioOutputTile from './config/AudioOutputTile';
import { useKrispNoiseFilter } from '@livekit/components-react/krisp';
import { TranscriptionTile } from '../../transcriptions/TranscriptionTile';
import {
  StyledAgentContainer,
  StyledVisualizerContainer,
  WidgetContainer,
} from './AppAgentView.styled';
import { useIntl } from 'react-intl';

interface VoiceAgentProps {
  onConnect: (shouldConnect: boolean) => void;
  config?: Record<string, unknown>;
}

const VoiceAgent: React.FC<VoiceAgentProps> = ({ onConnect, config }) => {
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

  /**
   * Cleanup effect - runs ONLY on unmount
   * IMPORTANT: Empty dependency array ensures this runs once on mount and cleanup on unmount only
   */
  useEffect(() => {
    return () => {
      // Cleanup all resources on unmount
      try {
        console.log('🧹 VoiceAgent cleanup starting (unmount only)...', {
          hasLocalParticipant: !!localParticipant,
          hasKrisp: !!krisp,
        });

        // Disable microphone
        if (localParticipant) {
          localParticipant.setMicrophoneEnabled(false);
          console.log('✅ Microphone disabled');
        }

        // Disable Krisp noise filter
        if (krisp) {
          krisp.setNoiseFilterEnabled(false);
          console.log('✅ Krisp noise filter disabled');
        }

        // Clear transcripts
        setTranscripts([]);
        console.log('✅ Transcripts cleared');

        console.log('✅ VoiceAgent cleanup completed');
      } catch (error) {
        console.error('❌ Error during VoiceAgent cleanup:', error);
      }
    };
  }, []); // Empty deps - cleanup only runs on unmount

  const localTracks = tracks.filter(({ participant }) => participant);
  const localMicTrack = localTracks.find(
    ({ source }) => source === Track.Source.Microphone,
  );

  const onDataReceived = useCallback(
    (msg) => {
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

  const chatTileContent = useMemo(() => {
    if (voiceAssistant.audioTrack) {
      return <TranscriptionTile agentAudioTrack={voiceAssistant.audioTrack} />;
    }
    return <></>;
  }, [voiceAssistant.audioTrack]);

  return (
    <WidgetContainer>
      {chatTileContent}
      <StyledAgentContainer direction="row">
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
            {/*{localMicTrack && (
                            <AudioInputTile config={config} trackRef={localMicTrack}/>
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
    </WidgetContainer>
  );
};

export default VoiceAgent;
