import React from 'react';
import { Card, Col, Row, Skeleton } from 'antd';
import styled from 'styled-components';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const StyledCard = styled(Card)`
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);

  .ant-card-body {
    padding: 16px !important;
  }
`;

const CardContent = styled.div`
  display: flex;
  align-items: center;
  gap: 24px;

  @media (max-width: ${({ theme }) => theme.breakpoints.md}px) {
    gap: 16px;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

const IconWrapper = styled.div`
  width: 64px;
  height: 64px;
  border-radius: 8px;
  border: 1px solid #ddd;
  padding: 12px;
  display: flex;
  align-items: center;
  justify-content: center;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 56px;
    height: 56px;
  }
`;

const ContentWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
`;

const RowBetween = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
`;

const DescriptionWrapper = styled.div`
  width: 80%;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

const ButtonWrapper = styled.div`
  min-width: 90px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

const FooterSkeleton = styled(SkeletonInput)`
  width: 20%;
  min-width: 50px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    width: 40%;
  }
`;

const AiAgentsSkeleton: React.FC = () => {
  const skeletonItems = Array.from({ length: 8 });

  return (
    <Row gutter={[16, 16]}>
      {skeletonItems.map((_, index) => (
        <Col xs={24} sm={12} md={12} lg={12} xl={12} key={index}>
          <StyledCard>
            <CardContent>
              <IconWrapper>
                <Skeleton.Image style={{ width: '80%', height: '80%' }} />
              </IconWrapper>

              <ContentWrapper>
                <SkeletonInput style={{ width: '60%', height: 18 }} />

                <RowBetween>
                  <DescriptionWrapper>
                    <SkeletonInput style={{ width: '100%', height: 14 }} />
                  </DescriptionWrapper>

                  <ButtonWrapper>
                    <SkeletonButton
                      size="large"
                      style={{
                        width: '100%',
                        height: 30,
                        borderRadius: 18,
                      }}
                    />
                  </ButtonWrapper>
                </RowBetween>

                <FooterSkeleton style={{ height: 14 }} />
              </ContentWrapper>
            </CardContent>
          </StyledCard>
        </Col>
      ))}
    </Row>
  );
};

export { AiAgentsSkeleton };
