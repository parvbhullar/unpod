'use client';
import React from 'react';
import { Card, Col, Divider, Row } from 'antd';
import SkeletonButton from 'antd/es/skeleton/Button';
import { SkeletonInput } from './common/SkeletonInput';

const EditBillingInfoSkeleton: React.FC = () => {
  return (
    <Card
      style={{
        maxWidth: 760,
        margin: '0 auto',
        borderRadius: 0,
        padding: 0,
        border: 'none',
      }}
      styles={{
        body: {
          padding: '0 ',
        },
      }}
    >
      <SkeletonInput style={{ width: 260, height: 32, marginBottom: 24 }} />

      <Row gutter={[16, 16]}>
        {Array.from({ length: 8 }).map((_, idx) => (
          <Col key={idx} xs={24} md={12}>
            <SkeletonInput block style={{ height: 40 }} />
          </Col>
        ))}

        <Col xs={24} md={12}>
          <SkeletonInput block style={{ width: '100%', height: 40 }} />
        </Col>
      </Row>

      <Divider style={{ margin: '32px 0 20px' }} />

      <SkeletonInput style={{ width: 180, height: 22, marginBottom: 16 }} />

      {Array.from({ length: 2 }).map((_, idx) => (
        <Row
          key={idx}
          gutter={[12, 12]}
          align="middle"
          style={{ marginBottom: 16, width: '100%' }}
        >
          <Col xs={24} md={10}>
            <SkeletonInput block style={{ width: '100%', height: 40 }} />
          </Col>
          <Col xs={24} md={10}>
            <SkeletonInput block style={{ width: '100%', height: 40 }} />
          </Col>
          <Col xs={24} md={4}>
            <SkeletonButton style={{ width: '100%', height: 40 }} />
          </Col>
        </Row>
      ))}

      <SkeletonButton style={{ width: 140, height: 36, marginBottom: 32 }} />

      <Divider />

      <Row justify="end" gutter={12}>
        <Col>
          <SkeletonButton style={{ width: 100, height: 40 }} />
        </Col>
        <Col>
          <SkeletonButton style={{ width: 120, height: 40 }} />
        </Col>
      </Row>
    </Card>
  );
};

export { EditBillingInfoSkeleton };
