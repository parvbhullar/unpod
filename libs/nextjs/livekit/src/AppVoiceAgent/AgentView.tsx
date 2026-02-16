import React, { useCallback, useEffect } from 'react';
import { LiveKitRoom } from '@livekit/components-react';
import VoiceAgent from './VoiceAgent';
import { useAgentConnection } from '../hooks/useAgentConnection';
import { useTokenGeneration } from '../hooks/useTokenGeneration';
import styled from 'styled-components';
import { ChatWidget } from './ChatWidget';
import { useAuthContext, useInfoViewActionsContext } from '@unpod/providers';

const CenteredContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 70px);
`;

type AgentViewProps = {
  spaceToken?: string;
  name?: string;
  agentName?: string;
  agentId?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  config?: Record<string, unknown>;
  [key: string]: unknown;
};

const AgentView: React.FC<AgentViewProps> = ({
  spaceToken,
  name,
  agentName,
  agentId,
  source,
  metadata,
  config,
  ...rest
}) => {
  const {
    roomToken,
    updateRoomToken,
    shouldConnect,
    wsUrl,
    connect,
    disconnect,
    setConnectionMode,
  } = useAgentConnection() as {
    roomToken: string | null;
    updateRoomToken: (token: string | null) => void;
    shouldConnect: boolean;
    wsUrl: string;
    connect: () => void;
    disconnect: () => void;
    setConnectionMode: (mode: string) => void;
  };
  const { user } = useAuthContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const roomRef = React.useRef<{ token?: string } | null>(null);
  const [startCall, setStartCall] = React.useState(false);

  // Use unified token generation hook
  const { generateToken: generateAgentToken } = useTokenGeneration({
    endpoint: `core/voice/generate_room_token/public_token/`,
    method: 'POST',
    cacheToken: true,
    onSuccess: (token: string, fullResponse: any) => {
      roomRef.current = fullResponse;
      updateRoomToken(token);
    },
  });

  const onStartVoice = useCallback(async () => {
    try {
      const token = await generateAgentToken({
        space_token: spaceToken,
        contact_name: name,
        agent_name: agentName,
        agent_handle: agentId,
        metadata: {
          email: user?.email,
          name: user?.full_name,
          contact_number: user?.phone_number,
        },
        source: source || undefined,
      });
      return token;
    } catch (error) {
      console.error('Failed to start agent voice:', error);
      throw error;
    }
  }, [generateAgentToken, spaceToken, name, agentName, agentId, user, source]);

  console.log('rest in AgentView', { roomToken, updateRoomToken });

  // Auto-generate token on mount
  useEffect(() => {
    onStartVoice().catch((error) => {
      console.error('Auto-start voice failed:', error);
    });
  }, [onStartVoice]);

  // Use ref to track connection state to avoid callback recreation
  const connectionFunctionsRef = React.useRef({
    connect,
    disconnect,
    setConnectionMode,
  });

  // Keep ref updated without causing re-renders
  useEffect(() => {
    connectionFunctionsRef.current = { connect, disconnect, setConnectionMode };
  }, [connect, disconnect, setConnectionMode]);

  // Auto-connect when token is available (runs only when token changes)
  useEffect(() => {
    if (roomToken) {
      console.log('🔌 Auto-connecting with roomToken');
      setConnectionMode('env');
      connect();
    }
  }, [roomToken]); // Only depend on roomToken, not handleConnect

  // Stable callback for VoiceAgent to prevent cleanup loop
  const handleVoiceAgentConnect = useCallback(
    (shouldConnect: boolean) => {
      // Always use 'env' mode for agent view
      if (shouldConnect) {
        connectionFunctionsRef.current.setConnectionMode('env');
        connectionFunctionsRef.current.connect();
      } else {
        connectionFunctionsRef.current.disconnect();
      }
    },
    [], // Stable - no dependencies
  );

  return (
    <LiveKitRoom
      serverUrl={wsUrl}
      token={roomToken ?? undefined}
      connect={shouldConnect}
      onError={(e) => {
        infoViewActionsContext.showError(e.message);
        console.error(e);
      }}
    >
      {startCall && roomToken ? (
        <CenteredContainer>
          <VoiceAgent
            config={config}
            onConnect={handleVoiceAgentConnect}
            setStartCall={setStartCall}
          />
        </CenteredContainer>
      ) : (
        <CenteredContainer>
          <ChatWidget
            {...rest}
            onClick={() => {
              setStartCall(true);
              if (roomRef.current?.token) {
                updateRoomToken(roomRef.current.token);
              }
            }}
          />
        </CenteredContainer>
      )}
    </LiveKitRoom>
  );
};

export default AgentView;
