import { useEffect, useMemo, useState } from 'react';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useAuthContext,
} from '@unpod/providers';
import { StyledSearchBoxWrapper } from './index.styled';
import AppList from '@unpod/components/common/AppList';
import { AppDocumentsSkeleton } from '@unpod/skeleton/AppDocumentsSkeleton';
import DocItem from './DocItem';
import SubHeader from '../../../../Sidebar/People/SubHeader';
import { getUtcTimestamp } from '@unpod/helpers/DateHelper';

const DocSelector = ({ allowSelection = false }) => {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});

  const { setSelectedDocs, connectorActions } = useAppSpaceActionsContext();
  const { selectedDocs, connectorData } = useAppSpaceContext();
  const { isAuthenticated } = useAuthContext();
  const { apiData, count, loading, isLoadingMore, page, hasMoreRecord } =
    connectorData || {};

  const { setLoadingMore, setQueryParams, setPage } = connectorActions || {};
  const records = connectorData?.apiData || [];
  const isDocsLoading = loading;

  const checkedType = useMemo(() => {
    if (selectedDocs?.length === records.length) {
      return 'all';
    } else if (selectedDocs.length === 0) {
      return 'none';
    } else {
      return 'partial';
    }
  }, [selectedDocs, records]);

  useEffect(() => {
    if (isAuthenticated) {
      setQueryParams({
        page: 1,
        search,
        ...filters,
        tag: filters?.tag ? filters?.tag : undefined,
        from_ts: filters?.from_ts
          ? getUtcTimestamp(filters?.from_ts)
          : undefined,
        to_ts: filters?.to_ts ? getUtcTimestamp(filters?.to_ts) : undefined,
      });
    }
  }, [filters, search, isAuthenticated]);

  const onToggleCheck = () => {
    if (checkedType === 'none') {
      setSelectedDocs(records.map((doc: any) => doc.document_id));
    } else {
      setSelectedDocs([]);
    }
  };
  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

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
          allowSelection={allowSelection}
          setFilters={setFilters}
        />
      </StyledSearchBoxWrapper>
      <AppList
        style={{
          height: 'calc(100vh - 120px)',
        }}
        data={apiData}
        initialLoader={<AppDocumentsSkeleton />}
        loading={loading}
        renderItem={(data, index) => <DocItem key={index} data={data} />}
        onEndReached={onEndReached}
        footerProps={{
          loading: isLoadingMore,
          showCount: count,
          hasMoreRecord: hasMoreRecord,
        }}
      />
    </>
  );
};

export default DocSelector;
