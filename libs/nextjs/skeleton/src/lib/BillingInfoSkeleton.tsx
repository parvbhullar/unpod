'use client';
import React from 'react';
import {Card, Col, Row, Skeleton} from 'antd';
import styled from 'styled-components';

const StyledWrapper = styled.div`
  display: flex;
  justify-content: center;
  padding: 40px 16px;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    padding: 14px;
  }
`;

const StyledCard = styled(Card)`
  width: 100%;
  max-width: ${({theme}) => theme.sizes.mainContentWidth} !important;
  border-radius: 12px;

  .ant-card-body {
    padding: 24px;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    max-width: 100%;
  }
`;

const Label = styled.div`
  color: #999;
`;

const BillingInfoSkeleton: React.FC = () => {
  return (
    <StyledWrapper>
      <StyledCard
        title={<Skeleton.Input active style={{width: 180, height: 24}}/>}
      >
        <Row gutter={[16, 16]}>
          {Array.from({length: 7}).map((_, idx) => (
            <React.Fragment key={idx}>
              <Col xs={24} sm={8}>
                <Label>
                  <Skeleton.Input active style={{width: '90%', height: 14}}/>
                </Label>
              </Col>
              <Col xs={24} sm={16}>
                <Skeleton.Input active style={{width: '100%', height: 16}}/>
              </Col>
            </React.Fragment>
          ))}
        </Row>

        <div style={{marginTop: 24}}>
          <Skeleton.Button active style={{width: 110, height: 36}}/>
        </div>
      </StyledCard>
    </StyledWrapper>
  );
};

export default BillingInfoSkeleton;
