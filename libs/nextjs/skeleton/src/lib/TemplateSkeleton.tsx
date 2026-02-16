'use client';
import React from 'react';
import { Card, Col, Row, Skeleton } from 'antd';
import styled from 'styled-components';

const StyledSkeleton = styled(Skeleton)`
  display: flex;
  flex-direction: column;
  align-items: center;

  .ant-skeleton-content {
    width: 100%;
    text-align: center;

    h3 {
      margin: 0 auto;
    }

    ul {
      margin: 12px 0 0 0 !important;
    }

    li {
      margin: 6px 0 0 0 !important;
    }
  }
`;

const TemplateSkeleton: React.FC = () => {
  return (
    <Row gutter={[12, 12]}>
      {Array.from({ length: 8 }).map((_, index) => (
        <Col span={12} key={index}>
          <Card bordered styles={{ body: { padding: 12 } }}>
            <StyledSkeleton
              active
              avatar={{ shape: 'circle', size: 40 }}
              title={{ width: '60%' }}
              paragraph={{
                rows: 5,
                width: ['100%', '100%', '100%', '100%', '50%'],
              }}
            />
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export { TemplateSkeleton };
