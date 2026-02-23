'use client';
import {useCallback} from 'react';
import VoiceAgent from './VoiceAgent';
import {useAgentConnection} from '@unpod/livekit/hooks/useAgentConnection';

const AgentView = ({spaceView = false}) => {
  const {setConnectionMode} = useAgentConnection() as any;

  // Stable callback for VoiceAgent to prevent cleanup loop
  const handleVoiceAgentConnect = useCallback(
    (connected: boolean) => {
      if (connected) {
        setConnectionMode('chat');
      }
    },
    [setConnectionMode],
  );

  // return  <div>hi</div>
  return (
    <VoiceAgent onConnect={handleVoiceAgentConnect} spaceView={spaceView}/>
  );
};

export default AgentView;
