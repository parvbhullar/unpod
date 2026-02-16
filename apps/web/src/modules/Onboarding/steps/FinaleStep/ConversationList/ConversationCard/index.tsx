import React, { useRef, useState } from 'react';
import { Flex, Typography } from 'antd';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import {
  CardWrapper,
  StyledButtonWrapper,
  StyledDescription,
  StyledPrimaryButton,
} from './index.styled';

const { Title } = Typography;

type ConversationAction = {
  label: string;
  playIcon: React.ReactNode;
  pauseIcon: React.ReactNode;
};

type ConversationItem = {
  label: string;
  description: string;
  icon?: React.ReactNode;
  action: ConversationAction;
};

type ConversationCardProps = {
  item: ConversationItem;
  agent?: {
    telephony_config?: {
      voice_profile_id?: string | number;
    };
  } | null;
};

const ConversationCard: React.FC<ConversationCardProps> = ({ item, agent }) => {
  const infoViewActionsContext = useInfoViewActionsContext();

  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isPlaying, setPlaying] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const onPlaySound = () => {
    if (fileUrl) {
      if (isPlaying) {
        audioRef.current?.pause();
        setPlaying(false);
      } else {
        audioRef.current?.play();
        setPlaying(true);
      }
    } else {
      setLoading(true);
      getDataApi<ArrayBuffer>(
        `/core/voices/${agent?.telephony_config?.voice_profile_id}/`,
        infoViewActionsContext,
        {},
        true,
        {},
        'arraybuffer',
      )
        .then((arrayBuffer) => {
          const blob = new Blob([arrayBuffer.data], { type: 'audio/mpeg' });
          const url = URL.createObjectURL(blob);

          audioRef.current = new Audio(url);
          setFileUrl(url);
          audioRef.current.play();
          audioRef.current.onended = () => {
            setPlaying(false);
          };
          setLoading(false);
          setPlaying(true);
        })
        .catch((response) => {
          const err = response as { message?: string };
          infoViewActionsContext.showError(err.message || 'Error');
          setLoading(false);
        });
    }
  };

  return (
    <CardWrapper>
      <Flex justify="start" align="center" gap="8px">
        {item.icon}
        <Title level={4} style={{ margin: 0 }}>
          {item.label}
        </Title>
      </Flex>
      <StyledDescription>{item.description}</StyledDescription>
      <StyledButtonWrapper>
        <StyledPrimaryButton
          icon={isPlaying ? item.action.pauseIcon : item.action.playIcon}
          loading={loading}
          onClick={onPlaySound}
        >
          {item.action.label}
        </StyledPrimaryButton>
      </StyledButtonWrapper>
    </CardWrapper>
  );
};

export default ConversationCard;
