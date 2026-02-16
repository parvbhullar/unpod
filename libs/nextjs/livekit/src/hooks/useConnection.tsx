'use client';

import React, {
  createContext,
  type ReactNode,
  useCallback,
  useState,
} from 'react';
import { useConfig } from './useConfig';

type ConnectionMode = 'manual' | 'env';

type ConnectionContextValue = {
  wsUrl: string;
  token: string;
  shouldConnect: boolean;
  mode: ConnectionMode;
  connect: (mode: ConnectionMode) => Promise<void>;
  disconnect: () => Promise<void>;};

const ConnectionContext = createContext<ConnectionContextValue | null>(null);

export const ConnectionProvider = ({ children }: { children: ReactNode }) => {
  const { config } = useConfig();
  const [connectionDetails, setConnectionDetails] = useState<{
    wsUrl: string;
    token: string;
    shouldConnect: boolean;
    mode: ConnectionMode;
  }>({
    wsUrl: '',
    token: '',
    shouldConnect: false,
    mode: 'manual',
  });

  const connect = useCallback(
    async (mode: ConnectionMode) => {
      let token = '';
      let url = '';

      console.log(
        'process.env.NEXT_PUBLIC_LIVEKIT_URL',
        process.env.NEXT_PUBLIC_LIVEKIT_URL,
      );
      if (mode === 'env') {
        if (!process.env.NEXT_PUBLIC_LIVEKIT_URL) {
          throw new Error('NEXT_PUBLIC_LIVEKIT_URL is not set');
        }
        url = process.env.NEXT_PUBLIC_LIVEKIT_URL;
        const params = new URLSearchParams();
        if (config.settings.room_name) {
          params.append('roomName', config.settings.room_name);
        }
        if (config.settings.participant_name) {
          params.append('participantName', config.settings.participant_name);
        }

        console.log('params', params);
        const { accessToken } = await fetch(
          `/api/token/livekit/?${params}`,
        ).then((res) => res.json());
        token = accessToken;
      } else {
        token = config.settings.token;
        url = config.settings.ws_url;
      }
      console.log('config.settings', config.settings);
      setConnectionDetails({ wsUrl: url, token, shouldConnect: true, mode });
    },
    [
      config.settings.token,
      config.settings.ws_url,
      config.settings.room_name,
      config.settings.participant_name,
    ],
  );

  const disconnect = useCallback(async () => {
    setConnectionDetails((prev) => ({ ...prev, shouldConnect: false }));
  }, []);

  return (
    <ConnectionContext.Provider
      value={{
        wsUrl: connectionDetails.wsUrl,
        token: connectionDetails.token,
        shouldConnect: connectionDetails.shouldConnect,
        mode: connectionDetails.mode,
        connect,
        disconnect,
      }}
    >
      {children}
    </ConnectionContext.Provider>
  );
};

export const useConnection = () => {
  const context = React.useContext(ConnectionContext);
  if (!context) {
    throw new Error('useConnection must be used within a ConnectionProvider');
  }
  return context;
};
