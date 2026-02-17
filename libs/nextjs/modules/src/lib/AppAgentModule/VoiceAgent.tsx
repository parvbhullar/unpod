import { useAuthContext } from '@unpod/providers';
import { StyledAgentRoot } from './index.styled';
import AppVoiceAgent from '@unpod/livekit/AppVoiceAgent/index';
import type { Pilot } from '@unpod/constants/types';

type VoiceAgentProps = {
  agentData: Pilot;
};

const VoiceAgent = ({ agentData }: VoiceAgentProps) => {
  const { user } = useAuthContext() || {};

  const firstName = user?.first_name || '';
  const lastName = user?.last_name || '';

  return (
    <StyledAgentRoot>
      <AppVoiceAgent
        spaceToken={user?.active_space?.token as string | undefined}
        agentId={agentData?.handle}
        agentName={agentData?.name}
        name={`${firstName} ${lastName}`.trim()}
        email={user?.email}
        conatctName={`${firstName} ${lastName}`.trim()}
      />
    </StyledAgentRoot>
  );
};

export default VoiceAgent;
