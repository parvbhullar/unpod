import type {VoiceProfile} from '@unpod/constants/types';

import {useGetDataApi} from '@unpod/providers';
import AppList from '@unpod/components/common/AppList';
import VoiceProfileCard from './VoiceProfileCard';

type VoiceProfilesProps = {
  onProfileSelect?: (profile: VoiceProfile | null) => void;
  id?: string | number;
  hideSelect?: boolean;
};

const VoiceProfiles = ({
                         onProfileSelect,
                         id,
                         hideSelect,
                       }: VoiceProfilesProps) => {
  const [{apiData, loading}] = useGetDataApi<VoiceProfile[]>(
    `/core/voice-profiles/`,
    {data: []},
  );

  return (
    <AppList
      loading={loading}
      emptyMessage="No voice profiles found"
      data={apiData?.data}
      renderItem={(item: VoiceProfile, index: number) => {
        return (
          <VoiceProfileCard
            key={index}
            data={item}
            onProfileSelect={onProfileSelect}
            hideSelect={hideSelect}
            selected={id === item.agent_profile_id}
          />
        );
      }}
    />
  );
};

export default VoiceProfiles;
