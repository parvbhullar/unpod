import React from 'react';
import dynamic from 'next/dynamic';
import { useIntl } from 'react-intl';
import { useGetDataApi } from '@unpod/providers';
import { Typography } from 'antd';
import AppList from '@unpod/components/common/AppList';
import { VoiceProfileSkeleton } from '@unpod/skeleton';
import { StyledRoot } from './index.styled';
import type { VoiceProfile } from '@unpod/constants/types';

const { Paragraph } = Typography;

type VoiceProfilesProps = {
  profile?: VoiceProfile | null;
  onProfileSelect: (profile: VoiceProfile | null) => void;
};

const VoiceProfileCard = dynamic(
  () =>
    import(
      '@unpod/modules/AppAgentModule/VoiceForm/VoiceProfiles/VoiceProfileCard'
    ),
  { ssr: false },
);


const VoiceProfiles: React.FC<VoiceProfilesProps> = ({
  profile,
  onProfileSelect,
}) => {
  const { formatMessage } = useIntl();
  const [{ apiData, loading }] = useGetDataApi<VoiceProfile[]>(
    `/core/voice-profiles/`,
    {
      data: [],
    },
  );

  return (
    <StyledRoot>
      <Paragraph strong>
        {formatMessage({ id: 'identityOnboarding.allAvailableVoices' })}
      </Paragraph>
      {loading ? (
        <VoiceProfileSkeleton />
      ) : (
        <AppList
          data={apiData?.data || []}
          itemPadding={12}
          renderItem={(item: VoiceProfile) => (
            <VoiceProfileCard
              key={item.agent_profile_id}
              data={item as unknown as Record<string, unknown>}
              onProfileSelect={(profileData) =>
                onProfileSelect(profileData as VoiceProfile | null)
              }
              selected={profile?.agent_profile_id === item.agent_profile_id}
            />
          )}
        />
      )}
    </StyledRoot>
  );
};

export default VoiceProfiles;
