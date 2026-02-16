import React from 'react';
import { Flex, Skeleton } from 'antd';

import SkeletonButton from 'antd/es/skeleton/Button';

const HeaderSkeleton: React.FC = () => {
  return (
    <Flex
      justify="space-between"
      style={{
        width: '100%',
        marginTop: 10,
        marginBottom: 10,
        padding: '0 0 0 30px',
      }}
      align="center"
    >
      <Flex justify="flex-start" style={{ width: '100%' }}>
        <Skeleton
          title={false}
          paragraph={{
            rows: 1,
            width: ['10%'],
          }}
          style={{ margin: 0 }}
        />
      </Flex>
      <SkeletonButton size="large" style={{ width: 150, marginRight: 10 }} />
    </Flex>
  );
};

export { HeaderSkeleton };
