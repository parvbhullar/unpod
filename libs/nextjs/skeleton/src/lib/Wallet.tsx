'use client';
import React from 'react';
import {Table} from 'antd';
import styled from 'styled-components';
import {SkeletonInput} from './common/SkeletonInput';
import SkeletonButton from './common/SkeletonButton';

const StyledContainer = styled.div`
  flex: 1;
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius}
    ${({theme}) => theme.component.card.borderRadius} 0 0;
  box-shadow: ${({theme}) => theme.component.card.boxShadow};
`;

const columns = [
  {
    title: 'Date & Time',
    dataIndex: 'date',
    key: 'date',
    render: () => <SkeletonInput style={{width: 120}}/>,
  },
  {
    title: 'Credits',
    dataIndex: 'credits',
    key: 'credits',
    render: () => <SkeletonButton style={{width: 50, height: 20}}/>,
  },
  {
    title: 'Amount',
    dataIndex: 'amount',
    key: 'amount',
    render: () => <SkeletonButton style={{width: 50, height: 20}}/>,
  },
  {
    title: 'Type',
    dataIndex: 'type',
    key: 'type',
    render: () => <SkeletonInput style={{width: 100}}/>,
  },
  {
    title: 'Via',
    dataIndex: 'via',
    key: 'via',
    render: () => <SkeletonInput style={{width: 80}}/>,
  },
];

const data = Array.from({length: 8}).map((_, i) => ({
  key: i,
}));

const WalletSkeleton: React.FC = () => {
  return (
    <StyledContainer>
      <Table columns={columns} dataSource={data} pagination={false} bordered/>
    </StyledContainer>
  );
};

export {WalletSkeleton};
