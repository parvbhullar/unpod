import React, { useCallback, useEffect } from 'react';
import { LiveKitRoom } from '@livekit/components-react';
import VoiceAgent from '../VoiceAgent';
import { useAgentConnection } from '../../hooks/useAgentConnection';
import { useTokenGeneration } from '../../hooks/useTokenGeneration';
import { useAuthContext, useInfoViewActionsContext } from '@unpod/providers';
import { CenteredContainer, TopContainer } from './AppAgentView.styled';
import { AppChatWidget } from './AppChatWidget';
import PreviousTests from './PreviousTests';

interface AppAgentViewProps {
  spaceToken?: string;
  name?: string;
  agentName?: string;
  agentId?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  config?: Record<string, unknown>;
  [key: string]: unknown;
}

const AppAgentView: React.FC<AppAgentViewProps> = ({
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
  } = useAgentConnection();
  const { user } = useAuthContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const roomRef = React.useRef(null);
  const [startCall, setStartCall] = React.useState(false);

  // Use unified token generation hook
  const { generateToken: generateAgentToken, isGenerating } =
    useTokenGeneration({
      endpoint: `core/voice/generate_room_token/public_token/`,
      method: 'POST',
      cacheToken: true,
      onSuccess: (token, fullResponse) => {
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
          email: user.email,
          name: user.full_name,
          contact_number: user.phone_number,
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

  const handleConnect = useCallback(
    async (shouldConnect, desiredMode) => {
      if (shouldConnect) {
        if (desiredMode) {
          connectionFunctionsRef.current.setConnectionMode(desiredMode);
        }
        connectionFunctionsRef.current.connect();
      } else {
        connectionFunctionsRef.current.disconnect();
      }
    },
    [], // Stable - no dependencies
  );

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
    (shouldConnect) => {
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

  const mockTests = [
    {
      id: '0011',
      time: '28:01',
      turns: 174,
      date: 'Just now',
      status: 'failed',
    },
    { id: '0010', time: '0:05', turns: 1, date: '28m ago', status: 'passed' },
    { id: '0009', time: '7:40', turns: 27, date: '28m ago', status: 'partial' },
    {
      id: '0011',
      time: '28:01',
      turns: 174,
      date: 'Just now',
      status: 'failed',
    },
    { id: '0010', time: '0:05', turns: 1, date: '28m ago', status: 'passed' },
    { id: '0009', time: '7:40', turns: 27, date: '28m ago', status: 'partial' },
    {
      id: '0011',
      time: '28:01',
      turns: 174,
      date: 'Just now',
      status: 'failed',
    },
    { id: '0010', time: '0:05', turns: 1, date: '28m ago', status: 'passed' },
    { id: '0009', time: '7:40', turns: 27, date: '28m ago', status: 'partial' },
  ];

  return (
    <LiveKitRoom
      serverUrl={wsUrl}
      token={roomToken}
      connect={shouldConnect}
      onError={(e) => {
        infoViewActionsContext.showError(e.message);
        console.error(e);
      }}
    >
      <TopContainer>
        <AppChatWidget
          {...rest}
          onClick={() => {
            setStartCall(true);
            updateRoomToken(roomRef.current?.token);
          }}
        />
      </TopContainer>

      {startCall && (
        <VoiceAgent
          config={config}
          onConnect={handleVoiceAgentConnect}
          agentName={agentName}
          setStartCall={setStartCall}
        />
      )}

      <PreviousTests tests={mockTests} startCall={startCall} />
    </LiveKitRoom>
  );
};

export default AppAgentView;
