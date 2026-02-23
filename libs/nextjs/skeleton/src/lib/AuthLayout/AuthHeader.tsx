import React from 'react';
import SkeletonButton from '../common/SkeletonButton';

const HeaderSkeleton: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'left',
        padding: '12px',
        position: 'fixed',
        top: 0,
        left: 50,
      }}
    >
      <SkeletonButton size="large" style={{width: 140}}/>
    </div>
  );
};

export {HeaderSkeleton};
