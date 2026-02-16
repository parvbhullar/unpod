import { Flex, Typography } from 'antd';
import { StyledButton, StyledFlex } from './index.styled';
import { RiRobot2Line } from 'react-icons/ri';
import { useIntl } from 'react-intl';
import type { Spaces } from '@unpod/constants/types';

const { Text } = Typography;

type AgentItem = {
  name?: string;
  space?: { slug?: string };
  [key: string]: unknown;
};

type LinkAgentItemProps = {
  item: AgentItem;
  currentSpace: Spaces | null;
  saveAgent: (agent: AgentItem) => void;
};

const LinkAgentItem = ({
  item,
  currentSpace,
  saveAgent,
}: LinkAgentItemProps) => {
  const { formatMessage } = useIntl();

  return (
    <StyledFlex
      key={item.name}
      justify="space-between"
      align="center"
      className={item?.space?.slug === currentSpace?.slug ? 'active' : ''}
    >
      <Flex gap={10}>
        <RiRobot2Line fontSize={18} />
        <Text strong>{item.name}</Text>
      </Flex>
      <StyledButton
        ghost
        size="small"
        type="primary"
        danger={item?.space?.slug === currentSpace?.slug}
        onClick={() => saveAgent(item)}
        className={item?.space?.slug === currentSpace?.slug ? 'Unlink' : ''}
      >
        {item?.space?.slug === currentSpace?.slug
          ? formatMessage({ id: 'drawer.unlink' })
          : formatMessage({ id: 'drawer.link' })}
      </StyledButton>
    </StyledFlex>
  );
};

export default LinkAgentItem;
