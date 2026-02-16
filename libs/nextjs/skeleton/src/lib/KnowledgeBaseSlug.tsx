'use client';
import React from 'react';
import { Card, Space, Table } from 'antd';
import styled from 'styled-components';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const StyledContainer = styled.div`
  flex: 1;
  background-color: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.component.card.borderRadius}
    ${({ theme }) => theme.component.card.borderRadius} 0 0;
  box-shadow: ${({ theme }) => theme.component.card.boxShadow};

  .ant-table-tbody > tr > td {
    border-bottom: none !important;
    border-top: none !important;
  }

  .ant-table-thead > tr > th {
    border-bottom: none !important;
    border-top: none !important;
  }
`;

const StyledCard = styled(Card)`
  border-radius: ${({ theme }) => theme.radius.base}px;
  .ant-card-body {
    padding: 12px !important;
  }
`;

const StyledCardContainer = styled.div`
  padding: 24px;
  border: 2px dashed ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
`;

const style = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 16,
  justifyContent: 'center',
  verticalAlign: 'middle',
};

type ButtonSkeletonProps = {
  width?: number;};

const ButtonSkeleton: React.FC<ButtonSkeletonProps> = ({ width = 100 }) => (
  <SkeletonButton size="default" style={{ width: width, height: 20 }} />
);

const columns = [
  {
    title: <SkeletonAvatar size="small" />,
    dataIndex: 'id',
    key: 'id',
  },
  {
    title: (
      <div style={style}>
        Name
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'name',
    key: 'name',
    render: () => <ButtonSkeleton width={70} />,
  },
  {
    title: (
      <div style={style}>
        Email
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'email',
    key: 'email',
    render: () => <ButtonSkeleton width={70} />,
  },
  {
    title: (
      <div style={style}>
        Contact Number
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'contact_number',
    key: 'contact_number',
    render: () => <ButtonSkeleton width={150} />,
  },
  {
    title: (
      <div style={style}>
        Alternate Contact Number <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'alternate_contact_number',
    key: 'alternate_contact_number',
    render: () => <ButtonSkeleton width={220} />,
  },
  {
    title: (
      <div style={style}>
        Occupation
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'occupation',
    key: 'occupation',
    render: () => <ButtonSkeleton width={120} />,
  },
  {
    title: (
      <div style={style}>
        Company Name
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'company_name',
    key: 'company_name',
    render: () => <ButtonSkeleton width={145} />,
  },
  {
    title: (
      <div style={style}>
        Address
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'address',
    key: 'address',
    render: () => <ButtonSkeleton width={90} />,
  },
  {
    title: (
      <div style={style}>
        About
        <SkeletonAvatar />
      </div>
    ),
    dataIndex: 'about',
    key: 'about',
    render: () => <ButtonSkeleton width={70} />,
  },
];

const skeletonData = Array.from({ length: 6 }).map((_, i) => ({
  key: i,
}));

const LoadingTable: React.FC = () => {
  return (
    <StyledContainer>
      <Table
        columns={columns}
        dataSource={skeletonData}
        pagination={false}
        size="middle"
        bordered
      />
    </StyledContainer>
  );
};

type CurrentKb = {
  content_type?: string;};

type LoadingConnectorsOrUploadProps = {
  currentKb?: CurrentKb;};

const LoadingConnectorsOrUpload: React.FC<LoadingConnectorsOrUploadProps> = ({
  currentKb,
}) => {
  return currentKb?.content_type === 'email' ? (
    <Card
      style={{
        borderRadius: 16,
        border: 'none',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
      }}
    >
      <Space orientation="vertical" align="center" size="large">
        <SkeletonButton style={{ width: 100, height: 32 }} />

        <Space size="large">
          {Array.from({ length: 2 }).map((_, i) => (
            <StyledCard key={i}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <SkeletonAvatar
                  shape="square"
                  size={30}
                  style={{ marginBottom: 8 }}
                />
                <SkeletonButton style={{ width: 70, height: 16 }} />
              </div>
            </StyledCard>
          ))}
        </Space>
      </Space>
    </Card>
  ) : (
    <Card
      style={{
        borderRadius: 16,
        border: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: 24,
          justifyContent: 'center',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <StyledCardContainer>
          <SkeletonAvatar size={48} style={{ marginBottom: 8 }} />
          <SkeletonInput style={{ width: 300, height: 20 }} size="small" />
        </StyledCardContainer>
        <SkeletonButton style={{ width: 200, height: 32 }} />
      </div>
    </Card>
  );
};

export { LoadingConnectorsOrUpload };
export { LoadingTable };
