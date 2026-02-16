import React, { CSSProperties } from 'react';
import { Skeleton } from 'antd';

type SkeletonInputProps = {
  style?: CSSProperties;
  size?: 'large' | 'small' | 'default';
  active?: boolean;
  block?: boolean;};

const SkeletonInput: React.FC<SkeletonInputProps> = ({ style, ...props }) => {
  return (
    <Skeleton.Input
      active
      style={
        style ? style : { display: 'flex', alignSelf: 'center', margin: 0 }
      }
      {...props}
    />
  );
};

export { SkeletonInput };
