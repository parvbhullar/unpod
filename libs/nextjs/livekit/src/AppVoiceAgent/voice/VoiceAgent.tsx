import '@livekit/components-styles';
import { ConfigurationPanelItem } from '../config/ConfigurationPanelItem';
import {
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useLocalParticipant,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react';
import {
  StyledVisualizerContainer,
} from '../Playground.styled';
import React, { useEffect, useState } from 'react';
import { useKrispNoiseFilter } from '@livekit/components-react/krisp';
import { WidgetContainer } from '../AgentView.styled';
import { useIntl } from 'react-intl';
import { ConnectionState } from 'livekit-client';
import AudioOutputTile from '../config/AudioOutputTile';
import styled from 'styled-components';

export const StyledAgentContainer = styled.div<{ $direction?: string }>`
  display: flex;
  flex-direction: ${({ $direction }) => $direction || 'row'};
  align-items: center;
  justify-content: center;
  width: 270px;
`;
type VoiceAgentProps = {
  onConnect: (shouldConnect: boolean) => void;
  config?: Record<string, unknown>;
  agentName?: string;
  setStartCall: (value: boolean) => void;
};

const VoiceAgent: React.FC<VoiceAgentProps> = ({
  onConnect,
  config,
  agentName,
  setStartCall,
}) => {
  const [, setTranscripts] = useState<
    {
      name: string;
      message: string;
      timestamp: number;
      isSelf: boolean;
    }[]
  >([]);
  const { localParticipant } = useLocalParticipant();
  const voiceAssistant = useVoiceAssistant();
  const roomState = useConnectionState();
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

  return (
    <WidgetContainer>
      <StyledAgentContainer $direction="row">
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
            onConnectClicked={() => {
              onConnect(false);
              setStartCall(false);
            }}
          />
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
