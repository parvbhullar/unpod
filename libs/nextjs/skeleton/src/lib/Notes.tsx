import React from 'react';
import styled from 'styled-components';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';

const StyledConversationItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 4px 8px;
`;

const StyledContent = styled.div`
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
`;

const StyledItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
`;

const NotesSkeleton: React.FC = () => {
  return (
    <StyledConversationItem>
      {[...Array(20)].map((_, idx) => (
        <StyledItem key={`item-${idx + 1}`}>
          <SkeletonAvatar size={32}/>
          <StyledContent>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
              }}
            >
              <SkeletonInput
                style={{width: 140, height: 14, minWidth: 140}}
              />
              <SkeletonInput
                style={{width: '20%', height: 10, minWidth: 90}}
              />
            </div>

            <SkeletonInput
              style={{
                width: '100%',
                height: 11,
                margin: 0,
              }}
            />

            <div
              style={{
                display: 'flex',
                gap: 6,
                alignItems: 'center',
              }}
            >
              <SkeletonInput
                style={{
                  width: 70,
                  height: 11,
                  minWidth: 50,
                  margin: 0,
                  display: 'block',
                }}
              />
              <SkeletonAvatar size={16}/>
              <SkeletonAvatar size={6}/>
            </div>
          </StyledContent>
        </StyledItem>
      ))}
    </StyledConversationItem>
  );
};

export {NotesSkeleton};
