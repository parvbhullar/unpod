import React from 'react';
import { Flex } from 'antd';
import { PiSpeakerSimpleHighBold } from 'react-icons/pi';
import { RiPauseLargeLine, RiPlayLargeLine } from 'react-icons/ri';
import ConversationCard from './ConversationCard';
import { useIntl } from 'react-intl';
import type { Pilot } from '@unpod/constants/types';

type ConversationListProps = {
  agent?: Pilot | null;
};

const ConversationList: React.FC<ConversationListProps> = ({ agent }) => {
  const { formatMessage } = useIntl();

  const cards = [
    {
      label: formatMessage({ id: 'onboarding.testVoice' }),
      description: formatMessage({ id: 'onboarding.testVoiceDesc' }),
      icon: <PiSpeakerSimpleHighBold fontSize={18} />,
      action: {
        label: formatMessage({ id: 'onboarding.playVoiceSample' }),
        playIcon: <RiPlayLargeLine size={18} />,
        pauseIcon: <RiPauseLargeLine size={18} />,
      },
    },
  ];

  return (
    <Flex justify="center" align="center" gap="24px">
      {cards.map((item, index) => (
        <ConversationCard key={index} item={item} agent={agent as any} />
      ))}
    </Flex>
  );
};

export default ConversationList;
