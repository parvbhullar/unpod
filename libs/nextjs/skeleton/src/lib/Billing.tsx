'use client';
import React from 'react';
import { Card, Col, Row, Skeleton } from 'antd';
import styled from 'styled-components';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';

const HeaderWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
`;

const HeaderLeft = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

const MainCard = styled(Card)`
  margin-bottom: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
`;

const CardContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const CardRow = styled(Col)`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const CardRowBottom = styled(Col)`
  display: flex;
  justify-content: space-between;
  align-items: center;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
`;

const SmallCardsRow = styled(Row)`
  margin-bottom: 24px;
  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
  }
`;

const SmallCard = styled(Card)`
  border-radius: 12px;
  margin-bottom: 16px;
`;

const SmallCardContent = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 16px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

const SmallCardText = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const TableCard = styled(Card)`
  margin-top: 16px;
`;

const TableRow = styled.div`
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
`;

const TableRowInner = styled.div`
  display: flex;
  gap: 50px;
  flex-wrap: wrap;
  width: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    gap: 16px;
    flex-direction: column;
  }
`;

const TableRowBottom = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
`;

const BillingSkeleton: React.FC = () => {
  const mobileScreen = useMediaQuery(MobileWidthQuery);

  return (
    <>
      <HeaderWrapper>
        <HeaderLeft>
          <Skeleton.Input active style={{ width: 100, height: 28 }} />
          <Skeleton.Input
            active
            style={{ width: mobileScreen ? 280 : 350, height: 18 }}
          />
        </HeaderLeft>
        <Skeleton.Button
          active
          size="large"
          style={{ width: 140, height: 35 }}
        />
      </HeaderWrapper>

      <MainCard>
        <CardContent>
          <CardRow>
            <Skeleton.Input active style={{ width: 120, height: 20 }} />
            <Skeleton.Input
              active
              style={{ width: mobileScreen ? 240 : 500, height: 16 }}
            />
          </CardRow>
          <CardRowBottom>
            <Skeleton.Input active style={{ width: 200, height: 14 }} />
            <Skeleton.Button active style={{ width: 100, height: 32 }} />
          </CardRowBottom>
        </CardContent>
      </MainCard>

      <SmallCardsRow gutter={[16, 16]}>
        {Array.from({ length: 3 }).map((_, idx) => (
          <Col xs={24} sm={24} md={8} key={idx}>
            <SmallCard>
              <SmallCardContent>
                <Skeleton.Avatar active shape="circle" size={32} />
                <SmallCardText>
                  <Skeleton.Input active style={{ width: 200, height: 20 }} />
                  <Skeleton.Button active style={{ width: 100, height: 24 }} />
                  <Skeleton.Input active style={{ width: 100, height: 18 }} />
                </SmallCardText>
              </SmallCardContent>
            </SmallCard>
          </Col>
        ))}
      </SmallCardsRow>

      <TableCard>
        <Skeleton.Input
          active
          style={{ width: 180, height: 20, marginBottom: 16 }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {Array.from({ length: 4 }).map((_, idx) => (
            <TableRow key={idx}>
              <TableRowInner>
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton.Input
                    active
                    key={i}
                    style={{ width: 100, height: 16 }}
                  />
                ))}
              </TableRowInner>
            </TableRow>
          ))}
          <TableRowBottom>
            {Array.from({ length: 2 }).map((_, idx) => (
              <Skeleton.Input
                active
                key={idx}
                style={{ width: 100, height: 16 }}
              />
            ))}
          </TableRowBottom>
        </div>
      </TableCard>
    </>
  );
};

export default BillingSkeleton;
