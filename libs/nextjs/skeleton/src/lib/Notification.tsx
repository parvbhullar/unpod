import React, { Fragment } from 'react';
import SkeletonButton from './common/SkeletonButton';
import { SkeletonInput } from './common/SkeletonInput';

const InvitationSkeleton: React.FC = () => {
  return (
    <div
      style={{
        borderRadius: 12,
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        width: 360,
      }}
    >
      {/* Title */}
      <SkeletonInput style={{ width: '60%', height: 16, borderRadius: 6 }} />

      {/* Subtitle (2 lines) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <SkeletonInput style={{ width: '90%', height: 13, borderRadius: 6 }} />
        <SkeletonInput style={{ width: '75%', height: 13, borderRadius: 6 }} />
      </div>

      {/* Buttons */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 12,
          marginTop: 8,
        }}
      >
        <SkeletonButton
          shape="round"
          style={{ width: 70, height: 28, borderRadius: 8 }}
        />
        <SkeletonButton
          shape="round"
          style={{ width: 70, height: 28, borderRadius: 8 }}
        />
      </div>
    </div>
  );
};

const Notification: React.FC = () => {
  return (
    <Fragment>
      {[...Array(10)].map((_, idx) => (
        <InvitationSkeleton key={idx} />
      ))}
    </Fragment>
  );
};

export { Notification };
