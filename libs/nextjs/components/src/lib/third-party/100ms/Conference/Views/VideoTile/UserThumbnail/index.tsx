import React, {CSSProperties, useMemo} from 'react';
import {selectPeerMetadata, selectPeerNameByID, useHMSStore,} from '@100mslive/react-sdk';
import UserAvatar from '../../../../../../common/UserAvatar';
import {AvatarContainer} from './index.styled';

type AvatarSize = 'small' | 'medium' | 'large';

interface UserThumbnailProps {
  peerId: string;
  avatarSize?: AvatarSize;
}

const UserThumbnail: React.FC<UserThumbnailProps> = ({peerId, avatarSize}) => {
  const metaData = useHMSStore(selectPeerMetadata(peerId));
  const peerName = useHMSStore(selectPeerNameByID(peerId));

  const style = useMemo((): CSSProperties => {
    if (avatarSize) {
      let avatarStyle: CSSProperties = {display: 'flex', alignItems: 'center'};
      if (avatarSize === 'small') {
        avatarStyle = {
          ...avatarStyle,
          fontSize: '0.75rem',
          height: '3rem',
          minHeight: '3rem',
          width: '3rem',
        };
      } else if (avatarSize === 'medium') {
        avatarStyle = {
          ...avatarStyle,
          fontSize: '1.5rem',
          height: '4rem',
          minHeight: '4rem',
          width: '4rem',
        };
      } else if (avatarSize === 'large') {
        avatarStyle = {
          ...avatarStyle,
          fontSize: '2rem',
          height: '5rem',
          minHeight: '5rem',
          width: '5rem',
        };
      }

      return avatarStyle;
    }

    return {
      fontSize: '1.5rem',
      height: '5rem',
      minHeight: '5rem',
      width: '5rem',
      display: 'flex',
      alignItems: 'center',
    };
  }, [avatarSize]);

  return (
    <AvatarContainer>
      <UserAvatar
        data-testid="participant_avatar_icon"
        user={{...metaData, ...metaData?.user_detail, full_name: peerName}}
        style={style}
      />
    </AvatarContainer>
  );
};

export default React.memo(UserThumbnail);
