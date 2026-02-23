import React from 'react';
import {Card, Col, Divider, Flex, Row, Skeleton} from 'antd';
import styled from 'styled-components';
import SkeletonButton from './common/SkeletonButton';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';

const StickyHeader = styled.div`
  position: sticky;
  top: 0;
  z-index: 99;
  background: #fff;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    position: static;
  }
`;

const TopActionButtons = styled(Col)`
  margin: 0 auto;
  width: 100% !important;
  max-width: ${({theme}) => theme.sizes.mainContentWidth} !important;
  display: flex;
  gap: 16px;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    max-width: 100%;
    padding-left: 0;
  }
`;

const SkeletonRow = styled(Row)`
  width: 100%;
  max-width: ${({theme}) => theme.sizes.mainContentWidth} !important;
  gap: 10px;
  justify-content: center;
  padding-left: 24px;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    max-width: 100%;
    padding-left: 0;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    padding: 0 16px;
    justify-content: flex-start;
  }
`;

const MainContainer = styled.div`
  width: 70%;
  margin: 0 auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 20px;

  @media (max-width: ${({theme}) => theme.breakpoints.lg}px) {
    width: 90%;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    width: 100%;
    padding: 12px;
  }
`;

const TwoColumnBlock = styled.div`
  display: flex;
  gap: 24px;
  width: 100%;
  margin-bottom: 24px;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    flex-direction: column;
  }
`;

const LeftColumn = styled.div`
  display: flex;
  gap: 32px;
  flex-direction: column;
  width: 100%;
`;

const SkeletonImageBox = styled.div`
  width: 140px;
  height: 120px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;

  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    width: 100%;
    height: 160px;
  }
`;

const FooterActions = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-bottom: 24px;

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    justify-content: center;
  }
`;

const StyledCard = styled(Card)`
  border-radius: 8px !important;

  .ant-card-body {
    padding: 16px !important;
  }

  .ant-card-head {
    padding: 8px 10px !important;
    min-height: unset !important;
  }

  .ant-card-head-title {
    padding: 0 !important;
  }
`;

const StyledFlex = styled(Flex)`
  flex-wrap: wrap;

  .ant-skeleton {
    width: auto !important;
  }
`;

const PurposeCard = styled(Card)`
  border-radius: 12px;
  text-align: center;

  .ant-card-body {
    padding: 10px !important;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
`;
const AiIdentityStudioSkeleton: React.FC = () => {
  return (
    <>
      <StickyHeader>
        <Row justify="space-between" align="middle" style={{padding: 16}}>
          <Col
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 10,
              width: 300,
            }}
          >
            <StyledFlex align="center" gap={10}>
              <SkeletonAvatar size="default"/>
              <SkeletonInput block style={{width: '70%', height: 25}}/>
              <SkeletonAvatar size="default"/>
            </StyledFlex>
          </Col>

          <TopActionButtons>
            {[1, 2, 3].map((i) => (
              <SkeletonButton key={i} style={{width: 140, height: 30}}/>
            ))}
            <SkeletonAvatar size="default"/>
          </TopActionButtons>
        </Row>

        <Divider style={{marginTop: 0}}/>

        <SkeletonRow gutter={16}>
          {[1, 2, 3].map((i) => (
            <Col key={i}>
              <SkeletonButton style={{width: 90, height: 30}}/>
            </Col>
          ))}
        </SkeletonRow>

        <Divider style={{marginTop: 24}}/>
      </StickyHeader>

      <MainContainer>
        <TwoColumnBlock>
          <LeftColumn>
            <SkeletonInput style={{width: '100%', height: 40}}/>

            <StyledCard
              title={<SkeletonInput block style={{width: 80, height: 20}}/>}
            >
              <SkeletonInput block style={{width: '100%', height: 40}}/>
            </StyledCard>
          </LeftColumn>

          <SkeletonImageBox>
            <Skeleton.Image active style={{width: '100%', height: '100%'}}/>
          </SkeletonImageBox>
        </TwoColumnBlock>

        <SkeletonInput block style={{width: 80, height: 20}}/>

        <Row gutter={[24, 24]}>
          {Array.from({length: 3}).map((_, idx) => (
            <Col xs={24} sm={12} md={8} key={idx}>
              <PurposeCard>
                <SkeletonAvatar size={36}/>
                <SkeletonInput block style={{width: '70%', height: 18}}/>
                <SkeletonInput block style={{width: '100%', height: 16}}/>
                <Skeleton.Input block style={{width: '80%', height: 14}}/>
              </PurposeCard>
            </Col>
          ))}
        </Row>

        <SkeletonInput
          block
          style={{width: '100%', height: 100, marginTop: 32}}
        />

        <Divider/>

        <FooterActions>
          <SkeletonButton size="large" style={{width: 120}}/>
        </FooterActions>
      </MainContainer>
    </>
  );
};

export {AiIdentityStudioSkeleton};
