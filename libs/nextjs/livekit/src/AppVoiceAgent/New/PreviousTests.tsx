import React from 'react';
import { Flex, Typography } from 'antd';
import {
  TestCard,
  TestInfo,
  TestMeta,
  TestsContent,
  TestsWrapper,
} from './PreviousTests.styled';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { MdOutlineWatchLater } from 'react-icons/md';
import { RiMessage2Line } from 'react-icons/ri';
import { SlCalender } from 'react-icons/sl'; // your badge component

const { Text } = Typography;

interface TestItem {
  id: string;
  time: string;
  turns: number;
  date: string;
  status: string;
}

interface PreviousTestsProps {
  tests: TestItem[];
  startCall: boolean;
}

const PreviousTests: React.FC<PreviousTestsProps> = ({ tests, startCall }) => {
  const statusColors = {
    passed: { label: 'Passed', color: 'badge-success' },
    failed: { label: 'Failed', color: 'badge-error' },
    partial: { label: 'Partial', color: 'badge-warning' },
  };

  return (
    <TestsWrapper>
      <Flex align="center" style={{ width: '100%' }} gap={12}>
        <Text strong>PREVIOUS TESTS</Text>
        <Text strong type="secondary">
          {tests.length}
        </Text>
      </Flex>

      <TestsContent $startCall={startCall}>
        {tests.map((test) => (
          <TestCard key={test.id}>
            <TestInfo>
              <Flex
                justify="space-between"
                align="center"
                style={{ width: '100%' }}
              >
                <Text strong>Test #{test.id}</Text>
                <AppStatusBadge
                  status={test.status}
                  statusColors={statusColors}
                  size="small"
                  shape="round"
                />
              </Flex>
              <TestMeta>
                <Flex align="center" gap={6}>
                  <MdOutlineWatchLater />
                  <Text type="secondary">{test.time}</Text>
                </Flex>
                <Flex align="center" gap={6}>
                  <RiMessage2Line />
                  <Text type="secondary">{test.turns} turns</Text>
                </Flex>
                <Flex align="center" gap={6}>
                  <SlCalender />
                  <Text type="secondary">{test.date}</Text>
                </Flex>
              </TestMeta>
            </TestInfo>
          </TestCard>
        ))}
      </TestsContent>
    </TestsWrapper>
  );
};

export default PreviousTests;
