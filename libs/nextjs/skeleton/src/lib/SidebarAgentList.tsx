import React from 'react';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';

type SidebarAgentListProps = {
  sidebarSize?: number;};

const SidebarAgentList: React.FC<SidebarAgentListProps> = ({
  sidebarSize = 20,
}) => {
  return (
    <div style={{ width: 280 }}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
          padding: '12px',
        }}
      >
        {[...Array(sidebarSize)].map((_, idx) => (
          <div
            key={idx}
            style={{ display: 'flex', alignItems: 'center', gap: 10 }}
          >
            <SkeletonAvatar shape="square" />
            <SkeletonInput style={{ width: 250, height: 25 }} />
          </div>
        ))}
      </div>
    </div>
  );
};

export { SidebarAgentList };
