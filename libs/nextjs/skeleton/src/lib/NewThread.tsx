import {Card} from 'antd';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';
import SkeletonAvatar from './common/SkeletonAvatar';

const NewThreadSkeleton = () => {
  return (
    <div
      style={{
        width: '760px',
        margin: '30px auto 0 auto',
        gap: 12,
      }}
    >
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 24,
          width: 400,
          margin: '0 auto 40px auto',
          textAlign: 'center',
        }}
      >
        <div>
          <SkeletonInput style={{width: 200, height: 28}}/>
        </div>
        <div>
          <SkeletonInput style={{width: 380, height: 22}}/>
        </div>
      </div>
      <Card
        style={{
          minHeight: 154,
          height: 154,
          width: '760px',
          borderRadius: 12,
          marginBottom: 6,
        }}
      >
        <div style={{display: 'flex', justifyContent: 'start'}}>
          <SkeletonInput
            style={{
              width: '40%',
              height: 14,
              marginBottom: 60,
            }}
          />
        </div>

        <div
          style={{
            display: 'flex',
            gap: 8,
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', gap: 12, alignItems: 'center'}}>
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
              <SkeletonAvatar size={20}/>
              <SkeletonInput
                style={{width: '20%', height: 20, minWidth: 90}}
              />
            </div>
            <SkeletonAvatar size={20}/>
          </div>
          <div style={{display: 'flex', gap: 12, alignItems: 'center'}}>
            <SkeletonAvatar size={20}/>
            <SkeletonButton size="large" style={{width: 90}}/>
          </div>
        </div>
      </Card>
    </div>
  );
};

export {NewThreadSkeleton};
