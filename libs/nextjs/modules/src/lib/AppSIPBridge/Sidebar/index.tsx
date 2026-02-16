'use client';
import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { MdOutlinePhone } from 'react-icons/md';
import { useAuthContext } from '@unpod/providers';
import { tablePageSize } from '@unpod/constants';
import { TAB_KEYS } from '../constants';
import AppSidebar from '@unpod/components/common/AppSidebar';
import {
  useAppModuleActionsContext,
  useAppModuleContext,
} from '@unpod/providers/AppModuleContextProvider';
import { SidebarAgentList } from '@unpod/skeleton';

const pageLimit = tablePageSize * 2;

const Sidebar = () => {
  const router = useRouter();
  const params = useSearchParams();
  const { listData, record } = useAppModuleContext() as any;
  const { apiData, loading, isLoadingMore, hasMoreRecord, page } = listData;
  const { listActions, setRecord, setIsNewRecord } =
    (useAppModuleActionsContext() as any) || {};
  const { setLoadingMore, setPage, setQueryParams } = listActions;
  const { isAuthenticated, activeOrg } = useAuthContext();

  useEffect(() => {
    if (isAuthenticated && activeOrg?.domain_handle) {
      setQueryParams({
        domain: activeOrg?.domain_handle,
        page_size: pageLimit,
        page: 1,
      });
    }
  }, [activeOrg, isAuthenticated]);

  const onClickAdd = () => {
    router.push(`/bridges/new/`);

    setIsNewRecord(true);
    setRecord(null);
  };

  const onSelectMenu = ({ key }: { key: string }) => {
    const record = apiData?.find((item: any) => item.slug === key);
    if (!record) return;
    setRecord(record);
    setIsNewRecord(false);
    const activeTab = params?.get('tab') || null;
    const routeUrl =
      activeTab && TAB_KEYS.includes(activeTab)
        ? `/bridges/${key}?tab=${activeTab}`
        : `/bridges/${key}`;
    router.push(routeUrl);
  };

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const onSearch = (value: string) => {
    setQueryParams({
      domain: activeOrg?.domain_handle,
      page_size: pageLimit,
      search: value,
      page: 1,
    });
  };

  const getMenuItems = () => {
    return apiData?.map((item: any) => ({
      key: item.slug,
      label: item.name,
      icon: <MdOutlinePhone fontSize={18} />,
    }));
  };

  if (!activeOrg?.domain_handle) return <SidebarAgentList />;

  return (
    <AppSidebar
      title="Voice Bridges"
      items={getMenuItems()}
      noDataMessage="No bridges found"
      loading={loading && !isLoadingMore}
      selectedKeys={[record?.slug || '']}
      onClickAdd={onClickAdd}
      onSelectMenu={onSelectMenu}
      onEndReached={onEndReached}
      isLoadingMore={isLoadingMore}
      onSearch={onSearch}
    />
  );
};

Sidebar.displayName = 'Bridge Sidebar';

export default Sidebar;
