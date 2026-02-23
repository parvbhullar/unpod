'use client';
import React, {Fragment} from 'react';
import styled from 'styled-components';
import {Card} from 'antd';
import SkeletonAvatar from './common/SkeletonAvatar';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

export const StyledGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 12px;
`;

type VoiceProfileGridSkeletonProps = {
  count?: number;
  hideSelect?: boolean;
};

const VoiceProfileGridSkeleton: React.FC<VoiceProfileGridSkeletonProps> = ({
                                                                             count = 6,
                                                                             hideSelect,
                                                                           }) => {
  return (
    <StyledGrid>
      <Fragment>
        {Array.from({length: count}).map((_, idx) => (
          <Card
            key={idx + 1}
            style={{
              marginBottom: 16,
              borderRadius: 12,
              width: '100%',
            }}
            styles={{
              body: {
                padding: '12px',
                width: '100%',
              },
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 10,
                width: '100%',
              }}
            >
              <SkeletonInput
                style={{width: 100, height: 18, minWidth: 100}}
                block={false}
              />
              <div style={{display: 'flex', gap: 10}}>
                <SkeletonInput
                  style={{width: 70, height: 13, minWidth: 70}}
                  block={false}
                />
                <SkeletonInput
                  style={{width: 70, height: 13, minWidth: 70}}
                  block={false}
                />
              </div>
              <SkeletonAvatar size={40}/>
            </div>
            <div style={{display: 'flex', gap: 8}}>
              {Array.from({length: 3}).map((_, idx) => (
                <SkeletonButton style={{width: 60, height: 18}}/>
              ))}
            </div>
          </Card>
        ))}
      </Fragment>
    </StyledGrid>
  );
};

export {VoiceProfileGridSkeleton};
