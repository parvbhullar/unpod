'use client';
import React from 'react';
import styled from 'styled-components';
import { Card } from 'antd';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const StyledContainer = styled.div`
  flex: 1;
  border-radius: ${({ theme }) => theme.component.card.borderRadius}
    ${({ theme }) => theme.component.card.borderRadius} 0 0;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};
  margin: 40px;
`;

const HubSkeleton: React.FC = () => {
  return (
    <div style={{ display: 'flex', width: '900px', margin: '0 auto 24px' }}>
      <StyledContainer>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            margin: '0 auto 24px',
            textAlign: 'center',
          }}
        >
          <SkeletonInput style={{ width: '50%', height: 20 }} active />
        </div>
        <Card
          style={{
            minHeight: 180,
            height: 180,
            borderRadius: 12,
            marginBottom: 32,
          }}
        >
          <SkeletonInput
            style={{ width: '40%', height: 14, marginBottom: 85 }}
          />

          <div
            style={{
              display: 'flex',
              gap: 8,
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
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
                <SkeletonAvatar size={20} active />
                <SkeletonInput
                  style={{ width: '20%', height: 20, minWidth: 90 }}
                />
              </div>
              <SkeletonAvatar size={20} active />
            </div>
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <SkeletonAvatar size={20} active />
              <SkeletonButton size="default" active />
            </div>
          </div>
        </Card>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 16,
          }}
        >
          {Array.from({ length: 3 }).map((_, idx) => (
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
                  style={{ width: 40, height: 20, minWidth: 110 }}
                />
                <SkeletonAvatar size={40} active />
              </div>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <SkeletonInput
                  style={{ width: '100%', height: 12, marginBottom: -4 }}
                  size="small"
                />
                <SkeletonInput
                  style={{ width: '100%', height: 12 }}
                  size="small"
                />
                <SkeletonInput
                  style={{ width: '40%', height: 12 }}
                  size="small"
                />
              </div>
            </Card>
          ))}
        </div>
      </StyledContainer>
    </div>
  );
};

export { HubSkeleton };
