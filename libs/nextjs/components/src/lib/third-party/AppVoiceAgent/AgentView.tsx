'use client';
import React, {useCallback, useEffect} from 'react';
import {LiveKitRoom} from '@livekit/components-react';
import {useInfoViewActionsContext} from '@unpod/providers';
import VoiceAgent from './VoiceAgent';
import {useAgentConnection} from '@unpod/livekit/hooks/useAgentConnection';

const AgentView = ({token, config}) => {
  const {shouldConnect, wsUrl, mode, connect, disconnect} =
    useAgentConnection();
  const infoViewActionsContext = useInfoViewActionsContext();

  const handleConnect = useCallback(
    async (c, mode) => {
      c ? connect(mode) : disconnect();
    },
    [connect, disconnect]
  );

  useEffect(() => {
    if (token) {
      handleConnect(true, 'env');
    }
  }, [token]);

  return (
    <LiveKitRoom
      serverUrl={wsUrl}
      token={token}
      connect={shouldConnect}
      onError={(e) => {
        infoViewActionsContext.showError(e.message);
        console.error(e);
      }}
    >
      <VoiceAgent
        config={config}
        onConnect={(c) => {
          const m = process.env.NEXT_PUBLIC_LIVEKIT_URL ? 'env' : mode;
          handleConnect(c, m);
        }}
      />
    </LiveKitRoom>
  );
};

export default AgentView;
