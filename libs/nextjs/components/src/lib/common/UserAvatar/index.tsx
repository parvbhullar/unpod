'use client';
import React, {useEffect, useState} from 'react';
import {getFirstLetter, getRandomColor} from '@unpod/helpers/StringHelper';
import {Avatar} from 'antd';
import {AvatarProps} from 'antd/es/avatar';
import {User} from './types';

type UserAvatarProps = AvatarProps & {
  user?: User;
  bgColor?: string;
  allowRandom?: boolean;
  fontSize?: number;
};

const UserAvatar: React.FC<UserAvatarProps> = ({
                                                 user,
                                                 bgColor,
                                                 allowRandom = true,
                                                 fontSize,
                                                 ...restProps
                                               }) => {
  const {style, ...avatarProps} = restProps;
  const [avatarSrc, setAvatarSrc] = useState<string | undefined>(
    user?.profile_picture || undefined,
  );
  const [profileColor, setProfileColor] = useState(
    allowRandom ? user?.profile_color || getRandomColor() : '#5071F6',
  );

  useEffect(() => {
    if (user?.profile_color && allowRandom) {
      setProfileColor(user?.profile_color);
    } else if (bgColor) {
      setProfileColor(bgColor);
    }
  }, [user, bgColor, allowRandom]);

  useEffect(() => {
    setAvatarSrc(user?.profile_picture || undefined);
  }, [user?.profile_picture]);

  const displayName =
    typeof user?.full_name === 'string'
      ? user.full_name
      : typeof user?.email === 'string'
        ? user.email
        : 'AI';

  return (
    <Avatar
      src={avatarSrc}
      style={{
        backgroundColor: profileColor,
        cursor: 'pointer',
        borderRadius: avatarProps.shape === 'square' ? 7 : undefined,
        fontSize,
        flexShrink: 0,
        ...style,
      }}
      onError={() => {
        setAvatarSrc(undefined);
        return false;
      }}
      {...avatarProps}
      alt={displayName || 'user'}
    >
      {getFirstLetter(displayName)}
    </Avatar>
  );
};

export default React.memo(UserAvatar);
