import React, { Fragment, useEffect, useMemo, useState } from 'react';
import { Flex, Typography } from 'antd';
import { RiMessage2Line } from 'react-icons/ri';
import { SlCalender } from 'react-icons/sl';
import {
  StyledFlex,
  TestCard,
  TestInfo,
  TestMeta,
  TestResultContent,
} from './PreviousTests.styled';
import { getTimeFromNow } from '@unpod/helpers';
import { TestItem, TestResultProps } from '@unpod/constants';
import { StatusColor, TestStatus } from './PreviousTests';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { IoEyeOutline } from 'react-icons/io5';
import AppDrawer from '@unpod/components/antd/AppDrawer';
import AppList from '@unpod/components/common/AppList';
import TestResultItem from './TestResultItem';

const { Text } = Typography;

type PreviousTestItemProps = {
  item: TestItem;
  statusColors: Record<TestStatus, StatusColor>;
};

const PreviousTestItem = ({ item, statusColors }: PreviousTestItemProps) => {
  const [showOutputDrawer, setShowOutputDrawer] = useState<boolean>(false);
  const [visibleItems, setVisibleItems] = useState<TestResultProps[]>([]);
  const [page, setPage] = useState(1);
  const itemsPerPage = 5;
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const createdText = useMemo(
    () => getTimeFromNow(item.created),
    [item.created],
  );

  useEffect(() => {
    if (!showOutputDrawer) {
      setPage(1);
      setVisibleItems(item.test_results?.slice(0, itemsPerPage) || []);
      setHasMore((item.test_results?.length || 0) > itemsPerPage);
    }
  }, [showOutputDrawer, item.test_results]);

  const loadMoreItems = () => {
    if (!hasMore || loadingMore) return;

    setLoadingMore(true);

    setTimeout(() => {
      const start = page * itemsPerPage;
      const end = start + itemsPerPage;
      const nextItems = item.test_results?.slice(start, end) || [];

      setVisibleItems((prev) => [...prev, ...nextItems]);
      setPage((prev) => prev + 1);
      setHasMore(end < (item.test_results?.length || 0));
      setLoadingMore(false);
    }, 200);
  };

  return (
    <Fragment>
      <TestCard>
        <TestInfo>
          <StyledFlex justify="space-between" align="center">
            <Text strong>Test #{1}</Text>
            <Flex align="center" gap={12}>
              <div
                style={{ cursor: 'pointer' }}
                onClick={() => setShowOutputDrawer(true)}
              >
                <IoEyeOutline size={16} />
              </div>
              <AppStatusBadge
                status={item.status}
                statusColors={statusColors}
                size="small"
                shape="round"
              />
            </Flex>
          </StyledFlex>
          <TestMeta>
            <Flex align="center" gap={6}>
              <RiMessage2Line />
              <Text type="secondary">{item.pass_rate} turns</Text>
            </Flex>
            <Flex align="center" gap={6}>
              <SlCalender />
              <Text type="secondary">{createdText}</Text>
            </Flex>
          </TestMeta>
        </TestInfo>
      </TestCard>

      <AppDrawer
        open={showOutputDrawer}
        onClose={() => setShowOutputDrawer(false)}
        closable
        title="Test Results"
        padding={'0'}
        size={500}
      >
        {showOutputDrawer && (
          <TestResultContent>
            <AppList
              data={visibleItems || []}
              renderItem={(item: TestResultProps) => (
                <TestResultItem item={item} />
              )}
              onEndReached={loadMoreItems}
              footerProps={{
                loading: loadingMore,
                footerText: hasMore ? '' : 'No more data',
                showCount: item.test_results.length,
                hasMoreRecord: hasMore,
              }}
            />
          </TestResultContent>
        )}
      </AppDrawer>
    </Fragment>
  );
};

export default React.memo(PreviousTestItem);
