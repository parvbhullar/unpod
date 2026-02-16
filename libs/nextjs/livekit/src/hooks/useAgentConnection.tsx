import React, {
  createContext,
  type ReactNode,
  useCallback,
  useState,
} from 'react';

type AgentConnectionMode = 'chat' | 'voice' | 'env' | null;

type AgentConnectionContextValue = {
  wsUrl?: string;
  roomToken: string | null;
  shouldConnect: boolean;
  connectionMode: AgentConnectionMode;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  updateRoomToken: (roomToken: string | null) => void;
  setConnectionMode: (mode: Exclude<AgentConnectionMode, null>) => void;};

const AgentConnectionContext =
  createContext<AgentConnectionContextValue | null>(null);

export const AgentConnectionProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [connectionDetails, setAgentConnectionDetails] = useState<{
    wsUrl?: string;
    roomToken: string | null;
    shouldConnect: boolean;
    connectionMode: AgentConnectionMode;
  }>({
    wsUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL,
    roomToken: null,
    shouldConnect: false,
    connectionMode: 'chat', // 'chat' or 'voice'
  });

  const updateRoomToken = (roomToken: string | null) => {
    // console.log("updateRoomToken roomToken",roomToken);
    setAgentConnectionDetails((prev) => ({ ...prev, roomToken: roomToken }));
  };

  const setConnectionMode = useCallback(
    (connectionMode: Exclude<AgentConnectionMode, null>) => {
      const validModes = ['chat', 'voice', 'env'];

      if (!validModes.includes(connectionMode)) {
        console.error(`❌ Invalid connection mode: ${connectionMode}`);
        return;
      }

      console.log('🔄 Connection mode changed to:', connectionMode);
      setAgentConnectionDetails((prev) => ({ ...prev, connectionMode }));
    },
    [],
  );

  const connect = useCallback(async () => {
    const url = process.env.NEXT_PUBLIC_LIVEKIT_URL;

    console.log(
      `🔌 Connecting to LiveKit (mode: ${connectionDetails.connectionMode})...`,
    );

    setAgentConnectionDetails((prev) => ({
      ...prev,
      wsUrl: url,
      shouldConnect: true,
    }));
  }, [connectionDetails.connectionMode]);

  const disconnect = useCallback(async () => {
    console.log('🔌 Disconnecting from LiveKit (preserving token)...');
    setAgentConnectionDetails((prev) => ({
      ...prev,
      shouldConnect: false,
      // Keep roomToken to allow reconnection without re-generating
      // Only clear connectionMode to indicate no active mode
      connectionMode: null,
    }));
  }, []);

  return (
    <AgentConnectionContext.Provider
      value={{
        wsUrl: connectionDetails.wsUrl,
        roomToken: connectionDetails.roomToken,
        shouldConnect: connectionDetails.shouldConnect,
        connectionMode: connectionDetails.connectionMode,
        connect,
        disconnect,
        updateRoomToken,
        setConnectionMode,
      }}
    >
      {children}
    </AgentConnectionContext.Provider>
  );
};

export const useAgentConnection = () => {
  const context = React.useContext(AgentConnectionContext);
  if (!context) {
    throw new Error(
      'useAgentConnection must be used within a AgentConnectionProvider',
    );
  }
  return context;
};
