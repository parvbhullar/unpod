import React from 'react';
import { Card } from 'antd';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';
import SkeletonButton from './common/SkeletonButton';

const SuperBooksSkeleton: React.FC = () => {
  return (
    <Card
      style={{
        minHeight: 217,
        height: 217,
        width: '760px',
        borderRadius: 12,
        marginBottom: 6,
        margin: '0 auto',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: 12,
          alignItems: 'center',
          marginBottom: 30,
          textAlign: 'center',
        }}
      >
        <SkeletonAvatar shape="square" size={30} style={{ borderRadius: 8 }} />
        <SkeletonInput style={{ width: '40%', height: 14, margin: 0 }} />
      </div>
      <SkeletonInput style={{ width: '60%', height: 14, marginBottom: 60 }} />

      <div
        style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div
            style={{
              height: 40,
              border: '1px solid #d9d9d9',
              borderRadius: 12,
              display: 'flex',
              alignItems: 'center',
              padding: 12,
              gap: 5,
            }}
          >
            <SkeletonAvatar size={20} />
            <SkeletonInput style={{ width: '20%', height: 20, minWidth: 90 }} />
          </div>
          <div
            style={{
              height: 40,
              border: '1px solid #d9d9d9',
              borderRadius: 12,
              display: 'flex',
              alignItems: 'center',
              padding: 12,
              gap: 5,
            }}
          >
            <SkeletonAvatar size={20} />
            <SkeletonInput style={{ width: '20%', height: 20, minWidth: 90 }} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <SkeletonAvatar size={40} />
          <SkeletonButton size="large" active style={{ width: 90 }} />
        </div>
      </div>
    </Card>
  );
};

export { SuperBooksSkeleton };
