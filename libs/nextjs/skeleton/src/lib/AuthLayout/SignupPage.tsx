'use client';
import React from 'react';
import {Card} from 'antd';
import styled from 'styled-components';
import {HeaderSkeleton} from './AuthHeader';
import SkeletonButton from '../common/SkeletonButton';
import {SkeletonInput} from '../common/SkeletonInput';
import SkeletonAvatar from '../common/SkeletonAvatar';

const StyledCard = styled(Card)`
  border-radius: ${({theme}) => theme.radius.base}px;
  margin-top: 100px;
  .ant-card-body {
    padding: 16px !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 30px;
  }
`;

const SignUpSkeleton: React.FC = () => {
  return (
    <div>
      <HeaderSkeleton/>
      <StyledCard>
        <SkeletonInput size="large" style={{width: '100%', height: 25}}/>
        <SkeletonInput size="large" style={{width: 500}}/>
        <SkeletonInput size="large" style={{width: 500}}/>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
            marginTop: 10,
          }}
        >
          <div
            style={{
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <SkeletonAvatar/>
            <SkeletonInput
              size="large"
              style={{width: 140, height: 20, minWidth: 140}}
            />
          </div>
          <div style={{flexShrink: 0}}>
            <SkeletonInput
              size="large"
              style={{width: 140, height: 20, minWidth: 140}}
            />
          </div>
        </div>
        <SkeletonButton size="large" style={{width: 500}}/>
      </StyledCard>
    </div>
  );
};

export {SignUpSkeleton};
