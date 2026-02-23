'use client';
import React from 'react';
import {Card, Col, Divider, Row, Skeleton} from 'antd';
import styled from 'styled-components';
import SkeletonAvatar from './common/SkeletonAvatar';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const StyledStickyHeader = styled.div`
  position: sticky;
  top: 0;
  z-index: 99;
  background: #fff;
  backdrop-filter: blur(0px);
`;

const StyledHeaderContent = styled.div`
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 16px;
`;

const StyledHeaderRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
`;

const StyledButtonGroup = styled(Col)`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
`;

const StyledButtonRow = styled(Row)`
  margin: 0;
  padding: 14px 32px;
`;

const StyledMainContent = styled.div`
  padding: 14px 32px;
  overflow-y: auto;
  height: auto;
  display: flex;
  flex-direction: column;
  gap: 30px;
`;

const StyledInputBox = styled.div`
  width: 250px;
  height: 40px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  display: flex;
  padding: 8px;
  align-items: center;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    width: 100%;
  }
`;

const StyledRowBox = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  flex-wrap: wrap;
  gap: 16px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

const StyledInnerBox = styled.div`
  display: flex;
  gap: 5px;
  flex: 1;
`;

const StyledButtonInner = styled.div`
  width: 270px;
  height: 40px;
  border: 1px solid #d9d9d9;
  border-radius: 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    width: 100%;
    padding: 12px;
  }
`;

const StyledCard = styled(Card)`
  border-radius: 16px;
  margin-bottom: 24px;

  .ant-card-body {
    padding: 18px !important;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
`;

const StyledSkeleton = styled(Skeleton)`
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

type BridgeStudioSkeletonProps = {
  lastBox?: number;
};

const BridgeStudioSkeleton: React.FC<BridgeStudioSkeletonProps> = (
  props,
) => {
  const lastBox = props?.lastBox ?? 4;
  return (
    <div>
      <StyledStickyHeader>
        <StyledHeaderContent>
          <StyledHeaderRow>
            <SkeletonAvatar size="small" style={{marginRight: 10}}/>
            <SkeletonInput block style={{width: '20%', height: 30}}/>
            <StyledButtonGroup>
              <SkeletonButton style={{width: 100}}/>
              <SkeletonAvatar size="default"/>
            </StyledButtonGroup>
          </StyledHeaderRow>
        </StyledHeaderContent>
        <Divider style={{margin: 0}}/>
        <StyledButtonRow gutter={16}>
          {Array.from({length: 2}).map((_, idx) => (
            <Col key={idx}>
              <SkeletonButton style={{width: 90, height: 30}}/>
            </Col>
          ))}
        </StyledButtonRow>
        <Divider style={{marginBottom: 14, marginTop: 0}}/>
      </StyledStickyHeader>
      <StyledMainContent>
        <SkeletonInput block style={{width: '100%', height: 40}}/>
        <SkeletonInput block style={{width: '30%', height: 20}}/>
        <SkeletonInput active block style={{width: '60%', height: 20}}/>
        <StyledInputBox>
          <SkeletonAvatar size="small" style={{marginRight: 10}}/>
          <SkeletonInput block style={{width: '100%', height: 20}}/>
        </StyledInputBox>
        <SkeletonInput block style={{width: '30%', height: 20}}/>
        {Array.from({length: lastBox}).map((_, idx) => (
          <StyledRowBox key={idx}>
            <StyledInnerBox>
              <SkeletonAvatar size="small"/>
              <SkeletonInput block style={{width: '100%', height: 20}}/>
            </StyledInnerBox>
            <StyledButtonInner>
              <SkeletonAvatar size="small" shape="square"/>
              <SkeletonInput block style={{width: '90%', height: 20}}/>
              <SkeletonAvatar size="small"/>
            </StyledButtonInner>
          </StyledRowBox>
        ))}
      </StyledMainContent>
    </div>
  );
};

const StyledContainer = styled.div`
  padding: 24px;
`;

const StyledHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const StyledHeaderRowButtons = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
`;

const StyledCardGroup = styled(Row)`
  margin-top: 16px;
  justify-content: center;
`;

const IsNewStudioSkeleton: React.FC = () => {
  return (
    <StyledContainer>
      <StyledHeader>
        <StyledHeaderRowButtons>
          <SkeletonAvatar active size="small"/>
          <SkeletonInput block style={{width: '20%', height: 30}}/>
          <StyledButtonGroup>
            <SkeletonButton active style={{width: 100}}/>
            <SkeletonButton active style={{width: 100}}/>
            <SkeletonButton active style={{width: 100}}/>
          </StyledButtonGroup>
        </StyledHeaderRowButtons>
        <SkeletonInput
          block
          style={{width: '30%', height: 30, borderRadius: 0}}
        />
        <SkeletonInput block style={{width: '100%', height: 20}}/>
        <Divider style={{marginTop: 20}}/>
      </StyledHeader>
      <Row gutter={16}>
        {Array.from({length: 3}).map((_, idx) => (
          <Col key={idx}>
            <SkeletonButton active style={{width: 110, height: 20}}/>
          </Col>
        ))}
      </Row>
      <Divider style={{marginBottom: 20, marginTop: 0}}/>
      <StyledCardGroup gutter={[24, 24]}>
        {[1, 2, 3].map((item) => (
          <Col xs={24} md={8} key={item}>
            <StyledCard
              style={{
                boxShadow: '0 6px 12px rgba(0,0,0,0.05)',
                minHeight: 220,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 24,
                }}
              >
                <SkeletonAvatar active size={40}/>
                <SkeletonInput style={{width: 160, height: 25}}/>
                <StyledSkeleton
                  title={false}
                  paragraph={{rows: 5, width: ['100%']}}
                  active
                />
              </div>
            </StyledCard>
          </Col>
        ))}
      </StyledCardGroup>
      <div style={{marginTop: 40}}>
        <SkeletonButton
          active
          style={{width: 140, height: 40, borderRadius: 8}}
        />
      </div>
    </StyledContainer>
  );
};

export {BridgeStudioSkeleton, IsNewStudioSkeleton};
