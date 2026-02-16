import type { ComponentType } from 'react';
import React, { useEffect } from 'react';
import EmailListItem from './EmailListItem';
import GeneralListItem from './GeneralListItem';
import ContactListItem from './ContactListItem';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useAuthContext,
} from '@unpod/providers';
import AppList from '../../common/AppList';
import { AppDocumentsSkeleton } from '@unpod/skeleton';

const LIST_COMPONENTS: Record<string, ComponentType<any>> = {
  email: EmailListItem,
  general: GeneralListItem,
  contact: ContactListItem,
};

type AppDocumentsProps = {
  search?: string;
  filters?: Record<string, any>;
  setDocsLoading: (loading: boolean) => void;};

const AppDocuments = ({
  search,
  filters,
  setDocsLoading,
}: AppDocumentsProps) => {
  const { connectorData, currentSpace } = useAppSpaceContext();
  const {
    apiData = [],
    count = 0,
    loading = false,
    isLoadingMore = false,
    page = 1,
    hasMoreRecord = false,
  } = connectorData;
  const { connectorActions } = useAppSpaceActionsContext();
  const { isAuthenticated } = useAuthContext();
  const { setLoadingMore, setQueryParams, setPage } = connectorActions;

  useEffect(() => {
    if (isAuthenticated) {
      setQueryParams({
        page: 1,
        search,
        ...filters,
        tag: filters?.tag,
      });
    }
  }, [filters, search, isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) setQueryParams({ page });
  }, [page, isAuthenticated]);

  useEffect(() => {
    setDocsLoading(loading && !isLoadingMore);
  }, [loading, isLoadingMore]);

  const listKey = currentSpace?.content_type as keyof typeof LIST_COMPONENTS;
  const ListItem = LIST_COMPONENTS[listKey] || GeneralListItem;

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  return (
    <AppList
      style={{
        height: 'calc(100vh - 125px)',
      }}
      data={apiData}
      initialLoader={<AppDocumentsSkeleton />}
      loading={loading}
      renderItem={(data, index) => (
        <ListItem key={index} data={data} showTimeFrom />
      )}
      onEndReached={onEndReached}
      footerProps={{
        loading: isLoadingMore,
        showCount: count,
        hasMoreRecord: hasMoreRecord,
      }}
    />
  );
};

AppDocuments.displayName = 'AppDocuments';

export default React.memo(AppDocuments);
