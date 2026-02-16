import {
  StyledAgentHandle,
  StyledAgentInput,
  StyledIconWrapper,
} from './index.styled';
import { Typography } from 'antd';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';
import { MdOutlineLink } from 'react-icons/md';

const { Text } = Typography;

const AgentHandle = ({ agentData }: { agentData?: any }) => {
  return (
    <StyledAgentHandle>
      {agentData?.handle && (
        <StyledAgentInput className="space-agent-token">
          <Text type="secondary">
            <MdOutlineLink fontSize={16} />
          </Text>

          <Text type="secondary">{agentData?.handle || 'Agent Handle...'}</Text>

          <StyledIconWrapper>
            <AppCopyToClipboard text={agentData?.handle} showToolTip />
          </StyledIconWrapper>
        </StyledAgentInput>
      )}
    </StyledAgentHandle>
  );
};

export default AgentHandle;
