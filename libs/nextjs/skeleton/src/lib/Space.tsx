'use client';
import React from 'react';
import styled from 'styled-components';
import {Card, Divider} from 'antd';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';
import SkeletonButton from './common/SkeletonButton';

const StyledContainer = styled.div`
  flex: 1;
  border-radius: ${({theme}) => theme.component.card.borderRadius}
    ${({theme}) => theme.component.card.borderRadius} 0 0;
  box-shadow: ${({theme}) => theme.component.card.boxShadow};
  display: flex;
  justify-content: center;
  align-items: center;
`;

const StyledRoot = styled.div`
  display: flex;
  background-color: ${({theme}) => theme.palette.background.default};
  height: 100vh;
  flex-direction: column;
`;
const StyledHeaderRoot = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 24px 24px 0 24px;
`;

const SpaceHeader: React.FC = () => {
  return (
    <StyledHeaderRoot>
      <div
        style={{
          display: 'flex',
          gap: 4,
          flexDirection: 'column',
          width: '100%',
        }}
      >
        <div
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'center',
            borderRadius: 12,
            width: '100%',
          }}
        >
          <SkeletonAvatar size={36} shape="square"/>
          <SkeletonInput style={{width: '50%', height: 25}}/>
        </div>
        <SkeletonInput style={{width: '50%', height: 14}}/>
      </div>
      <SkeletonButton size="default" style={{width: 100, height: 32}}/>
    </StyledHeaderRoot>
  );
};

const SpaceSkeleton: React.FC = () => {
  return (
    <StyledRoot>
      <SpaceHeader/>
      <Divider/>
      <StyledContainer>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 245px)',
            gap: 16,
          }}
        >
          {Array.from({length: 3}).map((_, idx) => (
            <Card
              key={idx}
              style={{
                borderRadius: 12,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 12,
                }}
              >
                <SkeletonInput
                  style={{width: 40, height: 20, minWidth: 110}}
                />
                <SkeletonAvatar size={40}/>
              </div>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <SkeletonInput
                  style={{width: '100%', height: 12, marginBottom: -4}}
                  size="small"
                />
                <SkeletonInput
                  style={{width: '100%', height: 12}}
                  size="small"
                />
                <SkeletonInput
                  style={{width: '40%', height: 12}}
                  size="small"
                />
              </div>
            </Card>
          ))}
        </div>
      </StyledContainer>
    </StyledRoot>
  );
};

export {SpaceSkeleton};
