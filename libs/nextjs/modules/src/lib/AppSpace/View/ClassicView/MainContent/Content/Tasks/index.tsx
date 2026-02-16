import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import AppTable from '@unpod/components/third-party/AppTable';
import type { Spaces, TaskItem } from '@unpod/constants/types';
import {
  getDataApi,
  useInfoViewActionsContext,
  usePaginatedDataApi,
} from '@unpod/providers';
import AppLoadingMore from '@unpod/components/common/AppLoadingMore';
import AppColumnZoomView from '@unpod/components/common/AppColumnZoomView';
import { AppDrawer } from '@unpod/components/antd';
import { getColumns } from './columns';
import { StyledContainer, StyledRoot } from './index.styled';
import { downloadFile } from '@unpod/helpers/FileHelper';
import { getTableFilterData } from '@unpod/helpers/TableHelper';
import { CallLogsTableSkeleton } from '@unpod/skeleton';
import { useIntl } from 'react-intl';

type TasksHandle = {
  refreshData: () => void;
};

type TasksProps = {
  currentSpace: Spaces | null;
};

const AppTableAny = AppTable as any;

const Tasks = forwardRef<TasksHandle, TasksProps>(({ currentSpace }, ref) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [selectedCol, setSelectedCol] = useState<{ title?: string } | null>(
    null,
  );
  const [filterSortValue, updateFilterSortValue] = useState({
    sortedInfo: {},
    filteredInfo: {},
  });
  const { formatMessage } = useIntl();
  const handleSetSelectedCol = (value: unknown) => {
    setSelectedCol(value as { title?: string } | null);
  };

  const [
    { apiData, loading, refreshing, isLoadingMore, hasMoreRecord, page },
    {
      setQueryParams,
      setLoadingMore,
      setPage,
      updateInitialUrl,
      setRefreshing,
    },
  ] = usePaginatedDataApi(
    `tasks/space-task/${currentSpace?.token ?? ''}/`,
    [],
    {
      page: 1,
      page_size: 30,
    },
    false,
  ) as unknown as [
    {
      apiData: unknown[];
      loading: boolean;
      refreshing: boolean;
      isLoadingMore: boolean;
      hasMoreRecord: boolean;
      page: number;
    },
    {
      setQueryParams: (params: Record<string, unknown>) => void;
      setLoadingMore: (value: boolean) => void;
      setPage: (value: number) => void;
      updateInitialUrl: (url: string) => void;
      setRefreshing: (value: boolean) => void;
    },
  ];

  useEffect(() => {
    setQueryParams({
      page: 1,
      page_size: 30,
      ...getTableFilterData(filterSortValue),
    });
    setPage(1);
  }, [filterSortValue]);

  const onTableFilterChange = (pagination: any, filters: any, sorter: any) => {
    updateFilterSortValue({
      sortedInfo: sorter,
      filteredInfo: filters,
    });
  };
  useEffect(() => {
    if (currentSpace?.token) {
      updateInitialUrl(`tasks/space-task/${currentSpace?.token}/`);
    }
  }, [currentSpace?.token]);

  useImperativeHandle(ref, () => ({
    refreshData: () => {
      setRefreshing(true);
      setPage(1);
    },
  }));

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const onDownload = (item: any) => {
    // Implement download functionality here
    getDataApi<{ url?: string }>(
      'media/pre-signed-url/',
      infoViewActionsContext,
      {
        url: item.output?.recording_url,
      },
    )
      .then((res) => {
        if (res.data?.url) downloadFile(res.data.url);
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  return (
    <StyledRoot>
      <StyledContainer>
        {loading && <CallLogsTableSkeleton />}
        <AppTableAny
          rowKey="task_id"
          columns={
            getColumns(handleSetSelectedCol, onDownload, formatMessage) as any
          }
          dataSource={(apiData || []) as TaskItem[]}
          size="middle"
          loading={loading || refreshing}
          pagination={false}
          onChange={onTableFilterChange}
          onScrolledToBottom={onEndReached}
          allowGridActions
          configuration={{
            showSerialNoRow: false,
            allowEditorToolbar: false,
            allowCountFooter: false,
            allowFormula: false,
          }}
          extraHeight={20}
        />
        {isLoadingMore && <AppLoadingMore />}
      </StyledContainer>

      <AppDrawer
        title={selectedCol?.title}
        open={selectedCol !== null}
        destroyOnHidden={true}
        onClose={() => setSelectedCol(null)}
        styles={{ body: { padding: 0, position: 'relative' } }}
        width="60%"
      >
        <AppColumnZoomView selectedCol={selectedCol} />
      </AppDrawer>
    </StyledRoot>
  );
});

Tasks.displayName = 'Tasks';

export default Tasks;
