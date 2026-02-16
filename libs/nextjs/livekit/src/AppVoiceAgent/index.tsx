import React from 'react';
import { AgentConnectionProvider } from '../hooks/useAgentConnection';
import AgentView from './AgentView';

type AppVoiceAgentProps = {
  spaceToken?: string;
  name?: string;
  agentName?: string;
  agentId?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  config?: Record<string, unknown>;
  [key: string]: unknown;
};

const AppVoiceAgent: React.FC<AppVoiceAgentProps> = (props) => {
  return (
    <AgentConnectionProvider>
      <AgentView {...props} />
    </AgentConnectionProvider>
  );
};

export default AppVoiceAgent;
