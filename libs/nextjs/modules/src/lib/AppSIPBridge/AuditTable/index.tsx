'use client';
import AppTable from '@unpod/components/third-party/AppTable';
import AppLoadingMore from '@unpod/components/common/AppLoadingMore';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppPageHeader, {AppHeaderButton,} from '@unpod/components/common/AppPageHeader';
import {MdHistory, MdRefresh} from 'react-icons/md';
import {useAuthContext, useDownloadData, usePaginatedDataApi,} from '@unpod/providers';
import {getColumns} from './columns';
import {PiExportBold} from 'react-icons/pi';
import {useEffect, useState} from 'react';
import {getTableFilterData} from '@unpod/helpers/TableHelper';
import {Button} from 'antd';
import {CallLogsTableSkeleton} from '@unpod/skeleton';
import {useIntl} from 'react-intl';

const AuditTable = () => {
  const {activeOrg, isAuthenticated} = useAuthContext();
  const {formatMessage} = useIntl();

  const [filterSortValue, updateFilterSortValue] = useState({
    sortedInfo: {},
    filteredInfo: {},
  });

  const [
    {apiData, loading, refreshing, isLoadingMore, hasMoreRecord, page},
    {setLoadingMore, setQueryParams, setPage, setRefreshing},
  ] = usePaginatedDataApi(
    `metrics/call-logs/`,
    [],
    {
      page: 1,
      page_size: 30,
    },
    false,
  ) as any;

  console.log('AuditTable', {
    apiData,
    loading,
    refreshing,
    isLoadingMore,
    hasMoreRecord,
    page,
  });
  const {downloading, downloadData} = useDownloadData(
    'metrics/call-logs/?download=true',
    'call-logs.csv',
  );

  /*  useEffect(() => {
    if (activeOrg)
      updateFilterSortValue({
        sortedInfo: {},
        filteredInfo: {},
      });
  }, [activeOrg]);*/

  useEffect(() => {
    if (!isAuthenticated || !activeOrg) return;
    setQueryParams({
      page: 1,
      page_size: 30,
      ...getTableFilterData(filterSortValue),
    });
  }, [filterSortValue, isAuthenticated, activeOrg]);

  const onTableFilterChange = (pagination: any, filters: any, sorter: any) => {
    // Only update if values have changed
    updateFilterSortValue((prevState) => {
      const isSorterSame =
        JSON.stringify(prevState.sortedInfo) === JSON.stringify(sorter);
      const isFilterSame =
        JSON.stringify(prevState.filteredInfo) === JSON.stringify(filters);

      if (isSorterSame && isFilterSame) {
        return prevState; // No change, return previous state
      }

      return {
        sortedInfo: sorter,
        filteredInfo: filters,
      };
    });
  };

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const AppTableAny = AppTable as any;

  return (
    <>
      <AppPageHeader
        hideToggleBtn
        pageTitle={formatMessage({id: 'nav.callLogs'})}
        leftOptions={formatMessage({id: 'callLogs.description'})}
        titleIcon={<MdHistory fontSize={21}/>}
        rightOptions={
          <>
            <Button
              type="text"
              shape="circle"
              size="small"
              icon={<MdRefresh fontSize={21}/>}
              loading={refreshing}
              onClick={() => {
                setRefreshing(true);
                setPage(1);
              }}
            />
            {apiData?.length > 0 && (
              <AppHeaderButton
                type="primary"
                shape="round"
                ghost
                onClick={() => downloadData()}
                icon={<PiExportBold/>}
                loading={downloading}
                disabled={downloading}
              >
                {formatMessage({id: 'common.export'})}
              </AppHeaderButton>
            )}
          </>
        }
      />
      <AppPageContainer>
        {loading && apiData.length === 0 ? (
          <CallLogsTableSkeleton/>
        ) : (
          <AppTableAny
            rowKey="id"
            columns={getColumns(formatMessage) as any}
            dataSource={apiData || []}
            onChange={onTableFilterChange}
            loading={refreshing}
            pagination={false}
            onScrolledToBottom={onEndReached}
          />
        )}

        {isLoadingMore && <AppLoadingMore/>}
      </AppPageContainer>
    </>
  );
};

export default AuditTable;
