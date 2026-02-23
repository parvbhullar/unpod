'use client';
import React from 'react';
import {Table} from 'antd';
import styled from 'styled-components';
import SkeletonButton from './common/SkeletonButton';

const StyledContainer = styled.div`
  flex: 1;
  background-color: ${({theme}) => theme.palette.background.default};
  border-radius: ${({theme}) => theme.component.card.borderRadius}
    ${({theme}) => theme.component.card.borderRadius} 0 0;
  box-shadow: ${({theme}) => theme.component.card.boxShadow};
  overflow-x: auto;
`;

const StyledSkeletonButton = styled(SkeletonButton)`
  @media (max-width: ${({theme}) => theme.breakpoints.md}px) {
    width: 80px !important;
    height: 18px !important;
  }

  @media (max-width: ${({theme}) => theme.breakpoints.sm}px) {
    width: 60px !important;
    height: 16px !important;
  }
`;

const columns = [
  {
    title: 'Call ID',
    dataIndex: 'id',
    key: 'id',
    render: () => <StyledSkeletonButton style={{height: 20}}/>,
  },
  {
    title: 'Bridge Name',
    dataIndex: 'bridge',
    key: 'bridge',
    render: () => <StyledSkeletonButton style={{width: 95, height: 20}}/>,
  },
  {
    title: 'Call Type',
    dataIndex: 'call_type',
    key: 'call_type',
    render: () => <StyledSkeletonButton style={{width: 95, height: 20}}/>,
  },
  {
    title: 'Assistant Number',
    dataIndex: 'source_number',
    key: 'source_number',
    render: () => <StyledSkeletonButton style={{width: 130, height: 20}}/>,
  },
  {
    title: 'User Number',
    dataIndex: 'destination_number',
    key: 'destination_number',
    render: () => <StyledSkeletonButton style={{width: 95, height: 20}}/>,
  },
  {
    title: 'Call Start Time',
    dataIndex: 'start_time',
    key: 'start_time',
    render: () => <StyledSkeletonButton style={{width: 130, height: 20}}/>,
  },
  {
    title: 'Call End Time',
    dataIndex: 'end_time',
    key: 'end_time',
    render: () => <StyledSkeletonButton style={{width: 130, height: 20}}/>,
  },
  {
    title: 'Duration',
    dataIndex: 'call_duration',
    key: 'call_duration',
    render: () => <StyledSkeletonButton style={{width: 95, height: 20}}/>,
  },
  {
    title: 'Status',
    dataIndex: 'call_status',
    key: 'call_status',
    render: () => <StyledSkeletonButton style={{width: 95, height: 20}}/>,
  },
  {
    title: 'End Reason',
    dataIndex: 'end_reason',
    key: 'end_reason',
    render: () => <StyledSkeletonButton style={{width: 95, height: 20}}/>,
  },
];

const data = Array.from({length: 40}).map((_, i) => ({
  key: i,
}));

const CallLogsTableSkeleton: React.FC = () => {
  return (
    <StyledContainer>
      <Table
        columns={columns}
        dataSource={data}
        pagination={false}
        bordered
        scroll={{x: 'max-content'}}
        size="middle"
      />
    </StyledContainer>
  );
};

export {CallLogsTableSkeleton};
