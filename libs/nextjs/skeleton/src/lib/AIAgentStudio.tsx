'use client';
import React from 'react';
import { Card, Col, Divider, Flex, Row, Skeleton } from 'antd';
import styled from 'styled-components';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const StickyHeader = styled.div`
  position: sticky;
  top: 0;
  z-index: 99;
  background: #fff;
`;

const HeaderRow = styled(Flex)`
  padding: 16px;
`;

const HeaderLeft = styled(Col)`
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 300px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

const HeaderRight = styled(Col)`
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    display: none;
  }
`;

const StyledHeader = styled.div`
  align-items: center;
  gap: 10px;
  display: none;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    display: flex !important;
  }
`;

const TabsRow = styled.div`
  margin: 0 auto;
  width: 100% !important;
  max-width: ${({ theme }) => theme.sizes.mainContentWidth} !important;
  display: flex;
  gap: 16px;
  padding: 18px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    max-width: 100%;
    overflow-x: auto;
    padding: 18px;
  }
`;

const ContentWrapper = styled.div`
  width: 100%;
  max-width: ${({ theme }) => theme.sizes.mainContentWidth} !important;
  margin: 0 auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 20px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    width: 100%;
    max-width: 100%;
    padding: 14px;
  }
`;

const StyledCard = styled(Card)`
  width: 100%;
`;

const CardTitle = styled.div`
  display: flex;
  gap: 6px;
  align-items: center;
`;

const ImageRow = styled.div`
  display: flex;
  gap: 20px;
  align-items: baseline;
  margin-bottom: 10px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
`;

const ImageBox = styled.div`
  width: 100px;
  height: 100px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 80px;
    height: 80px;
  }
`;

const AgentStudioSkeleton: React.FC = () => {
  return (
    <>
      <StickyHeader>
        <HeaderRow justify="space-between" align="center">
          <HeaderLeft>
            <SkeletonInput block style={{ width: '70%', height: 20 }} />
          </HeaderLeft>

          <HeaderRight>
            <SkeletonButton style={{ width: 140 }} />
            <SkeletonButton style={{ width: 140 }} />
            <SkeletonButton style={{ width: 140 }} />
            <SkeletonAvatar size="default" />
          </HeaderRight>

          <StyledHeader>
            <SkeletonAvatar size="default" />
            <SkeletonAvatar size="default" />
          </StyledHeader>
        </HeaderRow>

        <Divider style={{ margin: 0 }} />

        <TabsRow>
          {Array.from({ length: 6 }).map((_, idx) => (
            <Col key={idx}>
              <SkeletonButton style={{ width: 90, height: 30 }} />
            </Col>
          ))}
        </TabsRow>

        <Divider style={{ margin: 0 }} />
      </StickyHeader>

      <ContentWrapper>
        {/* Card 1 */}
        <StyledCard
          title={
            <CardTitle>
              <SkeletonAvatar size="small" />
              <SkeletonInput style={{ width: 70, height: 20 }} />
            </CardTitle>
          }
        >
          <SkeletonInput
            block
            style={{ width: '100%', height: 60, marginBottom: 15 }}
          />
          <Row gutter={16}>
            <Col>
              <SkeletonButton style={{ width: 80 }} />
            </Col>
            <Col>
              <SkeletonButton style={{ width: 80 }} />
            </Col>
          </Row>
        </StyledCard>

        <StyledCard
          title={
            <CardTitle>
              <SkeletonAvatar size="small" />
              <SkeletonInput style={{ width: 70, height: 20 }} />
            </CardTitle>
          }
        >
          <SkeletonInput
            block
            style={{ width: '100%', height: 60, marginBottom: 15 }}
          />
          <SkeletonInput block style={{ width: '60%', height: 16 }} />
        </StyledCard>

        <StyledCard
          title={
            <CardTitle>
              <SkeletonAvatar size="small" />
              <SkeletonInput style={{ width: 70, height: 20 }} />
            </CardTitle>
          }
        >
          <ImageRow>
            <ImageBox>
              <Skeleton.Image
                active
                style={{ width: '100%', height: '100%' }}
              />
            </ImageBox>
            <SkeletonButton style={{ width: 140 }} />
          </ImageRow>

          <SkeletonInput block style={{ width: '95%', height: 20 }} />
        </StyledCard>
      </ContentWrapper>
    </>
  );
};

export { AgentStudioSkeleton };
