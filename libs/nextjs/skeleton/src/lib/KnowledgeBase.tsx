import { Card, Col, Row } from 'antd';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonAvatar from './common/SkeletonAvatar';
import styled from 'styled-components';

const StyledCard = styled(Card)`
  border-radius: 16px;
  .ant-card-body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 6px 14px !important;
  }
`;

function KnowledgeBaseCardSkeleton() {
  return (
    <Row gutter={[24, 24]}>
      {Array.from({ length: 16 }).map((_, idx) => (
        <Col xs={24} sm={12} xl={6} key={idx}>
          <StyledCard>
            <div style={{ display: 'flex', alignItems: 'left' }}>
              <SkeletonAvatar
                size="default"
                shape="square"
                style={{ borderRadius: 10, marginBottom: 10 }}
              />
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'stretch',
                width: '100%',
              }}
            >
              <SkeletonInput
                style={{ width: '70%', height: 18, marginBottom: 10 }}
              />
              <SkeletonInput style={{ width: '90%', height: 14 }} />
              <SkeletonInput style={{ width: '100%', height: 14 }} />
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 8,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <SkeletonAvatar size="small" />
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <SkeletonInput
                    style={{
                      width: 100,
                      height: 16,
                      margin: 0,
                      display: 'block',
                    }}
                  />
                </div>
              </div>
              <SkeletonAvatar size={16} />
            </div>
          </StyledCard>
        </Col>
      ))}
    </Row>
  );
}

export { KnowledgeBaseCardSkeleton };
