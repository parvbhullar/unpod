import React, { CSSProperties } from 'react';
import { Skeleton } from 'antd';

type SkeletonButtonProps = {
  shape?: 'circle' | 'round' | 'square' | 'default';
  size?: 'large' | 'small' | 'default';
  style?: CSSProperties;
  active?: boolean;
  block?: boolean;};

const SkeletonButton: React.FC<SkeletonButtonProps> = ({
  shape = 'round',
  size = 'small',
  style,
  ...props
}) => {
  return (
    <Skeleton.Button
      active
      shape={shape}
      size={size}
      style={style ? style : { width: 100, marginRight: 10 }}
      {...props}
    />
  );
};

export default SkeletonButton;
