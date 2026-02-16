import React, { Fragment } from 'react';
import { Card, Skeleton } from 'antd';
import styled from 'styled-components';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';

const StyldeCard = styled(Card)`
  border-radius: 16px;
  .ant-card-body {
    padding: 16px !important;
  }
`;

type CardWithImageProps = {
  count?: number;
  image?: boolean;
  secondText?: boolean;};

const CardWithImage: React.FC<CardWithImageProps> = ({
  count = 1,
  image = false,
  secondText = false,
}) => {
  return (
    <Fragment>
      {Array.from({ length: count }).map((_, idx) => (
        <StyldeCard key={idx}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <SkeletonInput
                style={{
                  width: 180,
                  height: 24,
                  borderRadius: 6,
                  marginBottom: 10,
                }}
              />

              {secondText && (
                <SkeletonInput
                  style={{
                    width: 250,
                    height: 24,
                    borderRadius: 6,
                  }}
                />
              )}

              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  alignItems: 'center',
                }}
              >
                <SkeletonInput
                  style={{ width: 120, height: 14, borderRadius: 6 }}
                />
                <SkeletonAvatar />
                <SkeletonInput
                  style={{
                    width: 120,
                    height: 14,
                    borderRadius: 6,
                  }}
                />
              </div>
            </div>

            {image && (
              <div
                style={{
                  position: 'relative',
                  borderRadius: 12,
                  maxWidth: 260,
                  minWidth: 210,
                  maxHeight: 130,
                  minHeight: 130,
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <Skeleton.Image
                  active
                  style={{
                    position: 'absolute',
                    height: '100%',
                    width: '100%',
                    inset: '0px',
                    objectFit: 'cover',
                    color: 'transparent',
                  }}
                />
              </div>
            )}
          </div>
        </StyldeCard>
      ))}
    </Fragment>
  );
};

const SharedWithMeSkeleton: React.FC = () => {
  return (
    <div
      style={{
        width: 760,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        margin: '14px auto 0 auto',
      }}
    >
      <CardWithImage image />
      <CardWithImage secondText />
      <CardWithImage image secondText />
      <CardWithImage secondText />
      <CardWithImage secondText />
    </div>
  );
};

export { SharedWithMeSkeleton };
