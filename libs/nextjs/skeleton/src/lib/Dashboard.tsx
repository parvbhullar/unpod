'use client';
import React from 'react';
import {Card, Col, Flex, Row, Skeleton} from 'antd';
import SkeletonAvatar from './common/SkeletonAvatar';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';
import styled from 'styled-components';

const StyledContainer = styled.div`
  flex: 1;
  width: 100%;
  min-height: 100%;
  padding: 24px;
  background-color: ${({theme}) => theme.palette.background.default};
  border-top-left-radius: ${({theme}) => theme.component.card.borderRadius};
  border-top-right-radius: ${({theme}) => theme.component.card.borderRadius};

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    padding: 16px;
  }
`;

const StyledGridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  width: 100%;

  @media (max-width: ${({theme}) => theme.breakpoints.xl}px) {
    grid-template-columns: repeat(3, 1fr);
  }

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    grid-template-columns: 1fr;
  }
`;

const StyledSkeleton = styled(Skeleton)`
  .ant-skeleton-title {
    margin-bottom: 8px !important;
  }

  .ant-skeleton-paragraph {
    margin: 0 !important;
    padding: 0 !important;
  }

  .ant-skeleton-paragraph > ul {
    margin: 0 !important;
    padding: 0 !important;
  }

  .ant-skeleton-paragraph > li:not(:last-child) {
    margin-bottom: -8px !important;
  }
`;

type DashboardSkeletonProps = {
  cards?: number;
};

const DashboardSkeleton: React.FC<DashboardSkeletonProps> = ({cards = 3}) => {
  return (
    <StyledContainer>
      <SkeletonInput
        style={{width: '100%', maxWidth: 250, height: 32, marginBottom: 24}}
      />
      <Row gutter={[16, 16]}>
        {Array.from({length: cards}).map((_, idx) => (
          <Col xs={24} sm={12} md={12} lg={8} xl={6} key={idx}>
            <Card
              style={{
                minHeight: 100,
                borderRadius: 12,
                width: '100%',
              }}
              styles={{
                body: {
                  display: 'flex',
                  alignItems: 'center',
                  width: '100%',
                },
              }}
            >
              <Flex align="center" style={{width: '100%'}} gap={12}>
                <SkeletonAvatar size={40}/>
                <Flex vertical style={{width: '100%'}} align="center">
                  <StyledSkeleton
                    title={true}
                    paragraph={{rows: 4, width: ['100%']}}
                    active
                  />
                </Flex>
                <Col>
                  <SkeletonAvatar size={40}/>
                </Col>
              </Flex>
            </Card>
          </Col>
        ))}
      </Row>

      <SkeletonInput
        style={{width: '100%', maxWidth: 150, height: 28, margin: '24px 0'}}
      />

      <StyledGridContainer>
        {Array.from({length: 6}).map((_, idx) => (
          <Card
            style={{borderRadius: 12, minHeight: 100, width: '100%'}}
            styles={{
              body: {
                padding: 12,
                width: '100%',
                alignItems: 'center',
              },
            }}
          >
            <Flex vertical>
              <SkeletonInput
                style={{width: '60px', height: 20, marginBottom: 12}}
              />
              <Flex justify="space-between" style={{width: '100%'}}>
                <Col>
                  <SkeletonInput style={{width: '70%', height: 32}}/>
                </Col>
                <Col>
                  <SkeletonButton
                    shape="square"
                    style={{width: 30, height: 30}}
                  />
                </Col>
              </Flex>
            </Flex>
          </Card>
        ))}
      </StyledGridContainer>
    </StyledContainer>
  );
};

export {DashboardSkeleton};
