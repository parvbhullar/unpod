'use client';
import React from 'react';
import { Table } from 'antd';
import styled from 'styled-components';
import SkeletonAvatar from './common/SkeletonAvatar';
import { SkeletonInput } from './common/SkeletonInput';

const TableWrapper = styled.div`
  width: 100%;
  overflow-x: auto;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    .ant-table {
      min-width: 600px;
    }
  }
`;

const StyledCellWrapper = styled.div`
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;

  .ant-skeleton-element {
    width: 80% !important;
  }

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    align-items: flex-start;

    .ant-skeleton-element {
      width: 100% !important;
    }
  }
`;

const ActionIcons = styled.div`
  display: flex;
  gap: 10px;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    gap: 6px;
  }
`;

const columns = [
  {
    title: 'Api Key',
    dataIndex: 'api_key',
    key: 'api_key',
    render: () => (
      <StyledCellWrapper>
        <SkeletonInput style={{ width: '100%', height: 20 }} />
        <ActionIcons>
          <SkeletonAvatar size={20} />
          <SkeletonAvatar size={20} />
        </ActionIcons>
      </StyledCellWrapper>
    ),
  },
  {
    title: 'Created',
    dataIndex: 'created',
    key: 'created',
    render: () => <SkeletonInput style={{ height: 20 }} />,
  },
  {
    title: 'Action',
    dataIndex: 'action',
    key: 'action',
    render: () => <SkeletonAvatar size={25} />,
  },
];

const data = Array.from({ length: 2 }).map((_, i) => ({
  key: i,
}));

const ApiKeySkeleton: React.FC = () => {
  return (
    <TableWrapper>
      <Table
        columns={columns}
        dataSource={data}
        pagination={false}
        bordered
        size="middle"
        scroll={{ x: true }}
      />
    </TableWrapper>
  );
};

export { ApiKeySkeleton };
