'use client';
import React, { Fragment } from 'react';
import { Col, Flex, Row } from 'antd';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';

const ConversationsSkeleton: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        padding: '16px',
      }}
    >
      {[...Array(20)].map((_, idx) => (
        <Fragment key={idx}>
          <Flex gap={8} align="center" style={{ width: '100%' }}>
            <SkeletonAvatar size={32} style={{ marginBottom: 8 }} />

            <Col xs={20} sm={21} md={22} lg={23} xl={23}>
              <Row justify="space-between" align="middle">
                <Col xs={14} sm={12} md={10} lg={8}>
                  <SkeletonInput style={{ width: '100%', height: 14 }} />
                </Col>
                <Col xs={8} sm={10} md={12} lg={8}>
                  <SkeletonInput
                    style={{ width: 70, height: 10, minWidth: 70 }}
                  />
                </Col>
              </Row>
              <Row style={{ marginTop: 4 }}>
                <Col xs={12} sm={10} md={8} lg={6}>
                  <SkeletonInput style={{ width: '100%', height: 11 }} />
                </Col>
              </Row>
            </Col>
          </Flex>
        </Fragment>
      ))}
    </div>
  );
};

export { ConversationsSkeleton };
