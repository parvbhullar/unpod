import { Flex, Typography } from 'antd';
import { TestsContent, TestsWrapper } from './PreviousTests.styled';
import { useGetDataApi } from '@unpod/providers';
import AppLoader from '@unpod/components/common/AppLoader';
import AppList from '@unpod/components/common/AppList';
import PreviousTestItem from './previousTestItem';
import { TestItem } from '@unpod/constants';
import { useEffect, useMemo } from 'react';

const { Text } = Typography;
export type TestStatus = 'passed' | 'failed' | 'partial';

type PreviousTestsProps = {
  agentId: string | number | undefined;
  startCall?: boolean;
};

export type StatusColor = {
  label: string;
  color: string;
};

const statusColors: Record<TestStatus, StatusColor> = {
  passed: { label: 'Passed', color: 'badge-success' },
  failed: { label: 'Failed', color: 'badge-error' },
  partial: { label: 'Partial', color: 'badge-warning' },
};

const getTestStatus = (passRate: string): TestStatus => {
  const rate = parseFloat(passRate);
  if (rate > 70) return 'passed';
  if (rate >= 40) return 'partial';
  return 'failed';
};

const PreviousTests = ({ agentId, startCall }: PreviousTestsProps) => {
  const [{ apiData, loading }, { reCallAPI }] = useGetDataApi(
    `core/tests/test-agent/${agentId}/`,
    { data: [] as TestItem[] },
  );

  const evaluationsWithStatus = useMemo(() => {
    return (
      apiData?.data?.map((item: TestItem) => ({
        ...item,
        status: getTestStatus(item.pass_rate),
      })) ?? []
    );
  }, [apiData?.data]);

  useEffect(() => {
    reCallAPI();
  }, [startCall]);

  return (
    <TestsWrapper>
      <Flex
        align="center"
        style={{ width: '100%', padding: '0 16px' }}
        gap={12}
      >
        <Text strong>PREVIOUS TESTS</Text>
        <Text strong type="secondary">
          {apiData?.count}
        </Text>
      </Flex>

      <TestsContent $startCall={startCall}>
        <AppList
          data={evaluationsWithStatus || []}
          renderItem={(item: TestItem) => (
            <PreviousTestItem item={item} statusColors={statusColors} />
          )}
        />
      </TestsContent>
      {loading && <AppLoader position={'absolute'}  />}
    </TestsWrapper>
  );
};

export default PreviousTests;
