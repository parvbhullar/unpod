import React from 'react';
import SkeletonAvatar from '../common/SkeletonAvatar';

type LayoutSidebarSkeletonProps = {
  topIcon?: number;
  bottomIcon?: number;};

const LayoutSidebarSkeleton: React.FC<LayoutSidebarSkeletonProps> = ({
  topIcon = 5,
  bottomIcon = 4,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '16px',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {[...Array(topIcon)].map((_, idx) => (
          <SkeletonAvatar key={idx} size="large" />
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {[...Array(bottomIcon)].map((_, idx) => (
          <SkeletonAvatar key={idx} size="default" />
        ))}
      </div>
    </div>
  );
};

export { LayoutSidebarSkeleton };
