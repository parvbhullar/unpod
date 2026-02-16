import React, { CSSProperties } from 'react';
import AvatarSkeleton from 'antd/es/skeleton/Avatar';

type SkeletonAvatarProps = {
  size?: number | 'small' | 'default' | 'large';
  style?: CSSProperties;
  shape?: 'circle' | 'square';
  active?: boolean;};

const SkeletonAvatar: React.FC<SkeletonAvatarProps> = ({
  size = 16,
  style,
  shape = 'circle',
  ...props
}) => {
  return (
    <AvatarSkeleton
      active
      size={size}
      shape={shape}
      style={
        style ? style : { display: 'flex', alignSelf: 'center', margin: 0 }
      }
      {...props}
    />
  );
};

export default SkeletonAvatar;
