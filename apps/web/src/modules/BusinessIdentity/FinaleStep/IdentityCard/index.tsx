import React from 'react';
import { Badge, Flex, Typography } from 'antd';
import { IoMdCheckmarkCircleOutline } from 'react-icons/io';
import { GENDERS, LANGUAGE } from '@unpod/constants/CommonConsts';
import { StyledSubTitle } from '../../../landing/AI/index.styled';
import ConfiguredItem from './ConfiguredItem';
import {
  StyledAvatar,
  StyledCardWrapper,
  StyledDetailsCard,
  StyledSectionTitle,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Text } = Typography;

export type AgentSummary = {
  name?: string;
  template?: { name?: string };
  voice_profile?: { name?: string; gender?: keyof typeof GENDERS | string };
  telephonyConfig?: {
    transcriber?: { language?: keyof typeof LANGUAGE | string };
  };
};

type IdentityCardProps = {
  agent?: AgentSummary | null;
};

const IdentityCard = ({ agent }: IdentityCardProps) => {
  const { formatMessage } = useIntl();
  const genderKey = agent?.voice_profile?.gender;
  const genderCode =
    (genderKey && (GENDERS as Record<string, string>)[String(genderKey)]) ||
    String(genderKey || '');
  const languageKey = agent?.telephonyConfig?.transcriber?.language;
  const language =
    (languageKey &&
      (LANGUAGE as Record<string, string>)[String(languageKey)]) ||
    String(languageKey || '');

  return (
    <StyledCardWrapper>
      <Flex vertical align="center" gap={12}>
        <StyledAvatar size={52}>
          {<IoMdCheckmarkCircleOutline size={32} />}
        </StyledAvatar>

        <StyledSectionTitle>
          {formatMessage({ id: 'identityOnboarding.readyToLaunch' })}
        </StyledSectionTitle>
        <StyledSubTitle>
          {formatMessage({ id: 'identityOnboarding.identityConfigured' })}
        </StyledSubTitle>

        <StyledDetailsCard>
          <ConfiguredItem
            label={formatMessage({ id: 'onboarding.identity' })}
            value={agent?.name || ''}
          />

          {agent?.template?.name && (
            <ConfiguredItem
              label={formatMessage({ id: 'identityOnboarding.template' })}
              value={<Text strong>{agent?.template?.name}</Text>}
            />
          )}

          <ConfiguredItem
            label={formatMessage({ id: 'identityOnboarding.voice' })}
            value={
              <Flex align="center" gap={5}>
                <Text strong>{agent?.voice_profile?.name}</Text>
                <Badge dot={true} status="default" />
                <Text strong>{genderCode}</Text>
                <Badge dot={true} status="default" />
                <Text strong>{language}</Text>
              </Flex>
            }
          />
        </StyledDetailsCard>
      </Flex>
    </StyledCardWrapper>
  );
};

export default IdentityCard;
