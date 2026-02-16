'use client';
import { Card, Skeleton } from 'antd';
import styled from 'styled-components';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonButton from 'antd/es/skeleton/Button';

export const StyledRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  padding: 14px !important;
`;

export const StyledTabs = styled.div`
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
`;

export const StyledInfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;

  @media (max-width: ${({ theme }) => theme.breakpoints.lg}px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    grid-template-columns: repeat(1, 1fr);
  }
`;

const StyledCard = styled(Card)`
  background: ${({ theme }) => theme.palette.background.component};
  width: 100% !important;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    .ant-card-body {
      padding: 14px;
    }
  }
`;

const StyledMainContent = styled.div`
  max-width: calc(${({ theme }) => theme.sizes.mainContentWidth});
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 24px;

  overflow: auto !important;
  height: calc(1000vh - 280px) !important;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    padding-top: 14px;
  }
`;

const PeopleOverviewSkeleton: React.FC = () => {
  return (
    <StyledRoot>
      <StyledMainContent>
        <StyledTabs>
          <SkeletonAvatar size={20} />
          <SkeletonInput style={{ width: 80, height: 18 }} />
        </StyledTabs>

        <StyledCard>
          <Skeleton active paragraph={{ rows: 4 }} />
        </StyledCard>

        <StyledTabs>
          <SkeletonAvatar size={20} />
          <SkeletonInput style={{ width: 80, height: 18 }} />
        </StyledTabs>

        <StyledInfoGrid>
          {[1, 2, 3, 4, 5, 6, 7].map((_, index) => (
            <Card
              key={index}
              styles={{
                body: {
                  display: 'flex',
                  flexDirection: 'column',
                  padding: 12,
                },
              }}
            >
              <SkeletonInput style={{ width: 80, height: 14 }} />
              <SkeletonButton active style={{ width: 80, height: 20 }} />
            </Card>
          ))}
        </StyledInfoGrid>
      </StyledMainContent>
    </StyledRoot>
  );
};

export { PeopleOverviewSkeleton };
