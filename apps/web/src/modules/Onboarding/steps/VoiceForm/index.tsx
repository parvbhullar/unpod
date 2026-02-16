'use client';
import React, { Fragment, useState } from 'react';
import { Button, Flex } from 'antd';
import { useIntl } from 'react-intl';
import VoiceProfiles from './VoiceProfiles';
import { FooterBar } from '@/modules/Onboarding/index.styled';
import dayjs from 'dayjs';
import type { Pilot, VoiceProfile } from '@unpod/constants/types';

type VoiceFormProps = {
  agent: Pilot;
  setAgent: React.Dispatch<React.SetStateAction<Pilot>>;
  updateAgentData: (
    formData: FormData,
    setLoading: React.Dispatch<React.SetStateAction<boolean>>,
    nextStep?: string,
  ) => void;
};

const VoiceForm: React.FC<VoiceFormProps> = ({
  agent,
  setAgent,
  updateAgentData,
}) => {
  const { formatMessage } = useIntl();
  const [profile, setProfile] = useState<VoiceProfile | null>(
    agent?.profile || null,
  );
  const [loading, setLoading] = useState(false);

  const onNext = () => {
    const telephonyConfig = {
      transcriber: {
        provider: profile?.transcriber?.provider || '',
        language: profile?.transcriber?.languages?.[0]?.code || 'en',
        model: profile?.transcriber?.model || '',
      },
      voice: {
        provider: profile?.voice?.provider || '',
        voice: profile?.voice?.voice || '',
        model: profile?.voice?.model || '',
      },
      quality: profile?.quality || 'good',
      voice_profile_id: profile?.agent_profile_id || null,
      telephony: [],
    };

    const formData = new FormData();
    const timeRanges = [
      {
        start: dayjs('8:00 AM', 'hh:mm A').format('HH:mm'),
        end: dayjs('8:00 PM', 'hh:mm A').format('HH:mm'),
      },
    ];
    formData.append('name', agent.name || '');
    formData.append('handle', agent.handle || '');
    formData.append('telephony_config', JSON.stringify(telephonyConfig));
    formData.append('telephony_enabled', String(agent.type === 'Voice'));
    formData.append('token', '250');
    formData.append(
      'chat_model',
      JSON.stringify({
        codename: profile?.chat_model?.codename,
        provider: profile?.chat_model?.provider,
      }),
    );
    formData.append(
      'embedding_model',
      JSON.stringify({
        codename: profile?.chat_model?.codename,
        provider: profile?.chat_model?.provider,
      }),
    );
    formData.append('temperature', String(profile?.temperature));
    formData.append('state', 'published');
    formData.append('provider', String(profile?.temperature || ''));
    formData.append(
      'calling_days',
      JSON.stringify(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
    );
    formData.append('calling_time_ranges', JSON.stringify(timeRanges));
    formData.append(
      'voice_temperature',
      String(profile?.voice_temperature || '1.1'),
    );
    formData.append('voice_speed', String(profile?.voice_speed || '1.0'));
    formData.append('voice_prompt', String(profile?.voice_prompt || ''));
    updateAgentData(formData, setLoading, '4');
    setAgent((prev) => ({
      ...prev,
      telephonyConfig,
    }));
  };

  const onProfileSelect = (nextProfile: VoiceProfile | null) => {
    setProfile(nextProfile);
  };

  return (
    <Fragment>
      <VoiceProfiles onProfileSelect={onProfileSelect} profile={profile} />

      <FooterBar>
        <Flex justify="space-between" gap="8px">
          <Button
            type="primary"
            disabled={!profile}
            onClick={() => onNext()}
            style={{ paddingLeft: 24, paddingRight: 24 }}
            loading={loading}
          >
            {formatMessage({ id: 'identityOnboarding.continue' })}
          </Button>
        </Flex>
      </FooterBar>
    </Fragment>
  );
};

export default VoiceForm;
