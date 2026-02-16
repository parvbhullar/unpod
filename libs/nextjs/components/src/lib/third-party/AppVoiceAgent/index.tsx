"use client";
import React from 'react';
import { AgentConnectionProvider } from '@unpod/livekit/hooks/useAgentConnection';
import AppVoiceQuery from './AppVoiceQuery';

const AppVoiceAgent = () => {
  return (
    <AgentConnectionProvider>
      <AppVoiceQuery />
    </AgentConnectionProvider>
  );
};

export default AppVoiceAgent;
