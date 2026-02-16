import { Card, Divider, Skeleton } from 'antd';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const SettingSkeleton = () => {
  return (
    <Card
      style={{
        width: 750,
        height: 400,
        margin: '18px auto',
        borderRadius: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        <SkeletonInput style={{ width: 120 }} />
        <SkeletonInput style={{ width: 120 }} />
      </div>
      <Divider />

      <div
        style={{
          display: 'flex',
          gap: 24,
          flexDirection: 'column',
        }}
      >
        <div style={{ display: 'flex', gap: 20 }}>
          <div
            style={{
              display: 'flex',
              gap: 24,
              flexDirection: 'column',
            }}
          >
            {Array.from({ length: 2 }).map((_, idx) => (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 24,
                }}
              >
                <SkeletonInput style={{ height: 40, width: 200 }} />
                <SkeletonInput style={{ height: 40, width: 200 }} />
              </div>
            ))}

            <SkeletonInput style={{ width: 422, height: 80, margin: '0' }} />
          </div>

          <Skeleton.Image active style={{ height: 150, width: 150 }} />
        </div>
        <SkeletonButton size="large" style={{ width: 120 }} />
      </div>
    </Card>
  );
};

export { SettingSkeleton };
