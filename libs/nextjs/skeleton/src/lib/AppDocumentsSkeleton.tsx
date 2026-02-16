import React, { Fragment } from 'react';
import styled from 'styled-components';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';
import { Flex } from 'antd';

const StyledContent = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;

  .ant-skeleton-paragraph {
    margin: 0 !important;
  }

  .ant-skeleton-paragraph li {
    height: 14px !important;
    margin: 0 !important;
  }

  .ant-skeleton-paragraph li:nth-child(2) {
    height: 12px !important;
    margin-top: 8px !important;
  }
`;

type AppDocumentsSkeletonProps = {
  time?: boolean;};

const AppDocumentsSkeleton: React.FC<AppDocumentsSkeletonProps> = ({
  time = false,
}) => {
  return (
    <div style={{ padding: '14px' }}>
      {[...Array(20)].map((_, idx) => (
        <Fragment key={`items-${idx + 1}`}>
          <div
            key={`item-${idx + 1}`}
            style={{
              display: 'flex',
              gap: 10,
              width: '100%',
              marginBottom: 24,
            }}
          >
            <SkeletonAvatar size={36} shape="circle" />

            <StyledContent>
              <div style={{ margin: '0', gap: '12px' }}>
                <Flex justify="space-between" align="center">
                  <SkeletonInput style={{ width: '50%', height: 14 }} />

                  {time && (
                    <SkeletonInput
                      style={{ width: 70, minWidth: 70, height: 11 }}
                    />
                  )}
                </Flex>
                <SkeletonInput style={{ width: '60%', height: 12 }} />
              </div>
            </StyledContent>
          </div>
        </Fragment>
      ))}
    </div>
  );
};

export { AppDocumentsSkeleton };
