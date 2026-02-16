import { useEffect, useMemo, useState } from 'react';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import AppList from '@unpod/components/common/AppList';
import { AppDocumentsSkeleton } from '@unpod/skeleton/AppDocumentsSkeleton';
import CallItem from './Item';
import SubHeader from './SubHeader';
import { StyledSearchBoxWrapper } from './index.styled';
import { getUtcTimestamp } from '@unpod/helpers/DateHelper';
import type { Dayjs } from 'dayjs';

type FiltersState = {
  call_type?: string;
  status?: string | string[];
  from_ts?: Date | Dayjs;
  to_ts?: Date | Dayjs;
};

const Call = () => {
  const [search, setSearch] = useState('');
  const [isDocsLoading, setDocsLoading] = useState(false);
  const [filters, setFilters] = useState<FiltersState>({});

  const { callsActions, setSelectedDocs } = useAppSpaceActionsContext();
  const { currentSpace, callsData, selectedDocs } = useAppSpaceContext();

  const {
    apiData = [],
    extraData,
    loading = false,
    isLoadingMore = false,
    page = 1,
    hasMoreRecord = false,
  } = callsData;

  const records = apiData || [];
  const selectedDocIds = (selectedDocs as Array<string | number>) ?? [];

  const checkedType = useMemo(() => {
    if (selectedDocIds.length === records.length && records.length > 0) {
      return 'all';
    } else if (selectedDocIds.length === 0) {
      return 'none';
    } else {
      return 'partial';
    }
  }, [selectedDocIds, records]);

  useEffect(() => {
    callsActions.setQueryParams({
      search: search || undefined,
      call_type: filters?.call_type === 'all' ? undefined : filters?.call_type,
      status:
        !filters?.status ||
        (Array.isArray(filters?.status) && filters?.status.length === 0) ||
        (Array.isArray(filters?.status) && filters?.status.includes('all')) ||
        filters?.status === 'all'
          ? undefined
          : Array.isArray(filters?.status)
            ? filters?.status.toString()
            : filters?.status,
      from_ts: filters?.from_ts ? getUtcTimestamp(filters?.from_ts) : undefined,
      to_ts: filters?.to_ts ? getUtcTimestamp(filters?.to_ts) : undefined,
      page: 1,
      page_size: 50,
    });
  }, [search, filters]);

  // Update API URL when filters or search changes
  useEffect(() => {
    if (currentSpace?.token) {
      callsActions.setAllowApiCall(true);
      callsActions.updateInitialUrl(`spaces/${currentSpace?.slug}/calls/`);
    }
  }, [currentSpace?.token]);

  const onToggleCheck = () => {
    if (checkedType === 'none') {
      setSelectedDocs(records.map((doc) => doc.task_id));
    } else {
      setSelectedDocs([]);
    }
  };

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      callsActions.setLoadingMore(true);
      callsActions.setPage(page + 1);
    }
  };

  useEffect(() => {
    setDocsLoading(loading);
  }, [loading]);

  return (
    <>
      <StyledSearchBoxWrapper>
        <SubHeader
          onToggleCheck={onToggleCheck}
          checkedType={checkedType}
          isDocsLoading={isDocsLoading}
          setSearch={setSearch}
          filters={filters}
          search={search}
          setFilters={setFilters}
        />
      </StyledSearchBoxWrapper>
      <AppList
        style={{
          height: 'calc(100vh - 125px)',
        }}
        data={apiData}
        initialLoader={<AppDocumentsSkeleton time={true} />}
        loading={loading}
        renderItem={(data, index) => <CallItem key={index} data={data} />}
        onEndReached={onEndReached}
        footerProps={{
          loading: isLoadingMore,
          showCount: extraData?.count,
          hasMoreRecord: hasMoreRecord,
        }}
      />
    </>
  );
};

export default Call;
