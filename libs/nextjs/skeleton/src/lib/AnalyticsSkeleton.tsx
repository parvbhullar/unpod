import React from 'react';
import { Card, Col, Row, Skeleton } from 'antd';
import styled from 'styled-components';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';

const CardsRow = styled(Row)`
  margin-bottom: 24px;
`;

const MetricCard = styled(Card)`
  border-radius: 10px;

  .ant-card-body {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
`;

const MetricFooter = styled.div`
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const MainCard = styled(Card)`
  border-radius: 12px;

  .ant-card-body {
    padding: 16px;
  }
`;

const CardTitle = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
`;

const ListItem = styled.div`
  padding-bottom: 24px;
`;

const ListRow = styled.div`
  display: flex;
  gap: 24px;
  align-items: center;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    gap: 14px;
  }
`;

const ListContent = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 15px;
`;

const ListHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ActionButtonWrapper = styled.div`
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
    display: flex;
    justify-content: flex-end;
  }
`;

const AnalyticsSkeleton: React.FC = () => {
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  return (
    <div>
      {/* Top Metric Cards */}
      <CardsRow gutter={[16, 16]}>
        {Array.from({ length: 4 }).map((_, i) => (
          <Col key={i} xs={24} sm={12} md={12} lg={6}>
            <MetricCard>
              <Skeleton active paragraph={false} title={{ width: '60%' }} />
              <MetricFooter>
                <Skeleton.Button active style={{ width: 80, height: 28 }} />
                <SkeletonAvatar size={20} />
              </MetricFooter>
            </MetricCard>
          </Col>
        ))}
      </CardsRow>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {Array.from({ length: 2 }).map((_, i) => (
          <MainCard
            title={
              <CardTitle>
                <SkeletonInput
                  active
                  style={{
                    width: mobileScreen ? 100 : 200,
                    height: 28,
                    minWidth: mobileScreen ? 100 : 200,
                  }}
                />
                <SkeletonInput
                  active
                  style={{
                    width: mobileScreen ? 60 : 150,
                    height: 18,
                    minWidth: mobileScreen ? 60 : 150,
                  }}
                />
              </CardTitle>
            }
          >
            {Array.from({ length: 5 }).map((_, i) => (
              <ListItem key={i}>
                <ListRow>
                  <SkeletonAvatar
                    active
                    size={mobileScreen ? 50 : 56}
                    shape="square"
                    style={{ borderRadius: 10 }}
                  />

                  <ListContent>
                    <ListHeader>
                      <SkeletonInput
                        style={{
                          width: mobileScreen ? 120 : 120,
                          height: 20,
                          minWidth: mobileScreen ? 120 : 120,
                        }}
                      />
                    </ListHeader>

                    <Skeleton.Input
                      active
                      style={{
                        width: mobileScreen ? 150 : '100%',
                        height: 12,
                        minWidth: mobileScreen ? 150 : '100%',
                      }}
                    />
                  </ListContent>

                  <ActionButtonWrapper>
                    <Skeleton.Button
                      active
                      shape="square"
                      style={{
                        width: mobileScreen ? 60 : 120,
                        height: 25,
                        minHeight: 25,
                        minWidth: mobileScreen ? 60 : 120,
                      }}
                    />
                  </ActionButtonWrapper>
                </ListRow>
              </ListItem>
            ))}
          </MainCard>
        ))}
      </div>
    </div>
  );
};

export default AnalyticsSkeleton;
