import React from 'react';
import { Badge, Flex, Typography } from 'antd';
import { useIntl } from 'react-intl';
import {
  StyledAvatar,
  StyledCardWrapper,
  StyledDetailsCard,
  StyledSectionTitle,
} from './index.styled';
import { StyledSubTitle } from '@/modules/landing/AI/index.styled';
import ConfiguredItem from '@/modules/Onboarding/steps/FinaleStep/IdentityCard/ConfiguredItem';
import { IoMdCheckmarkCircleOutline } from 'react-icons/io';
import { GENDERS, LANGUAGE } from '@unpod/constants/CommonConsts';
import type { Pilot } from '@unpod/constants/types';

const { Text } = Typography;

type IdentityCardProps = {
  agent?: Pilot | null;
};

const IdentityCard: React.FC<IdentityCardProps> = ({ agent }) => {
  const { formatMessage } = useIntl();
  const phone = (agent as any)?.telephony_config?.telephony?.map(
    (p: { number?: string }) => p.number,
  );
  const genderKey = (agent as any)?.voice_profile?.gender as
    | keyof typeof GENDERS
    | undefined;
  const genderCode = (genderKey && GENDERS[genderKey]) || genderKey;
  const languageKey = (agent as any)?.telephonyConfig?.transcriber?.language as
    | keyof typeof LANGUAGE
    | undefined;
  const language = (languageKey && LANGUAGE[languageKey]) || languageKey;

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
            label={formatMessage({ id: 'identityOnboarding.identity' })}
            value={agent?.name || ''}
          />

          {(agent as any)?.template?.name && (
            <ConfiguredItem
              label={formatMessage({ id: 'identityOnboarding.template' })}
              value={<Text strong>{(agent as any)?.template?.name}</Text>}
            />
          )}

          <ConfiguredItem
            label={formatMessage({ id: 'identityOnboarding.tone' })}
            value={(agent as any)?.conversation_tone || ''}
          />
          <ConfiguredItem
            label={formatMessage({ id: 'identityOnboarding.voice' })}
            value={
              <Flex align="center" gap={5}>
                <Text strong>{(agent as any)?.voice_profile?.name}</Text>
                <Badge dot={true} status="default" />
                <Text strong>{genderCode}</Text>
                <Badge dot={true} status="default" />
                <Text strong>{language}</Text>
              </Flex>
            }
          />
          <ConfiguredItem
            label={formatMessage({ id: 'identityOnboarding.phone' })}
            value={phone}
          />
        </StyledDetailsCard>
      </Flex>

      {/*<Flex justify="flex-start" align="center">*/}
      {/*  <Button type="primary" onClick={() => setIsWidgetOpen(true)}>*/}
      {/*    Launch Voice Identity*/}
      {/*  </Button>*/}
      {/*</Flex>*/}
    </StyledCardWrapper>
  );
};

export default IdentityCard;
