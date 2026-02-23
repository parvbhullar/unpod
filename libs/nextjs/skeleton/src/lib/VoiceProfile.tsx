'use client';
import React, {Fragment} from 'react';
import {Card, Col, Flex} from 'antd';
import SkeletonAvatar from './common/SkeletonAvatar';
import SkeletonButton from './common/SkeletonButton';
import {SkeletonInput} from './common/SkeletonInput';

type VoiceProfileSkeletonProps = {
  count?: number;
};

const VoiceProfileSkeleton: React.FC<VoiceProfileSkeletonProps> = ({
                                                                     count = 6,
                                                                   }) => {
  return (
    <Fragment>
      {Array.from({length: count}).map((_, idx) => (
        <Card
          key={idx}
          style={{
            marginBottom: 16,
            borderRadius: 12,
          }}
          styles={{body: {padding: 16}}}
        >
          <Flex align="center" justify="space-between" gap={12}>
            <Col flex="32px">
              <SkeletonAvatar size={40}/>
            </Col>

            <Col flex="auto">
              <Flex align="center" justify="space-between">
                <Flex align="center" gap={50}>
                  <SkeletonInput
                    block
                    active
                    style={{minWidth: 100, height: 18, marginBottom: 6}}
                  />
                  <Flex align="center" gap={12}>
                    <SkeletonInput
                      block
                      active
                      style={{minWidth: 80, height: 18, marginBottom: 6}}
                    />
                    <SkeletonInput
                      block
                      active
                      style={{
                        minWidth: 40,
                        height: 18,
                        marginBottom: 6,
                        borderRadius: 6,
                      }}
                    />
                  </Flex>
                </Flex>
                <SkeletonButton
                  style={{width: 70, height: 18, borderRadius: 0}}
                />
              </Flex>
              <Flex align="center" gap={12}>
                {Array.from({length: 2}).map((_, index) => (
                  <Flex gap={8} align="center" key={index}>
                    <SkeletonButton style={{width: 60, height: 14}}/>
                    <SkeletonInput
                      block
                      active
                      style={{
                        minWidth: 60,
                        height: 8,
                        lineHeight: 0.5,
                      }}
                    />
                    <SkeletonButton style={{width: 40, height: 18}}/>
                  </Flex>
                ))}
              </Flex>
            </Col>
          </Flex>
        </Card>
      ))}
    </Fragment>
  );
};

export {VoiceProfileSkeleton};
