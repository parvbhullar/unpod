'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { RiRobot2Line } from 'react-icons/ri';
import { useAuthContext } from '@unpod/providers';
import { tablePageSize } from '@unpod/constants';
import AppSidebar from '@unpod/components/common/AppSidebar';
import { TAB_KEYS } from '../../AppSIPBridge/constants';
import {
  useAppModuleActionsContext,
  useAppModuleContext,
} from '@unpod/providers/AppModuleContextProvider';
import { SidebarAgentList } from '@unpod/skeleton';
import type { Pilot } from '@unpod/constants/types';

const pageLimit = tablePageSize * 2;
type SidebarProps = {
  path: string;
  title: string;
  idKey?: string;
};

const Sidebar = ({ path, title, idKey = 'handle' }: SidebarProps) => {
  const router = useRouter();
  const params = useSearchParams();
  const { activeOrg } = useAuthContext();

  const { listData, record } = useAppModuleContext() as {
    listData: {
      apiData: any[];
      loading: boolean;
      isLoadingMore: boolean;
      hasMoreRecord: boolean;
      page: number;
    };
    record: Pilot;
  };
  const { apiData, loading, isLoadingMore, hasMoreRecord, page } = listData;
  const { listActions, setRecord, setIsNewRecord } =
    useAppModuleActionsContext() as any;
  const { setLoadingMore, setPage, setQueryParams } = listActions;

  useEffect(() => {
    if (activeOrg?.domain_handle) {
      setQueryParams({
        domain: activeOrg?.domain_handle,
        page_size: pageLimit,
        page: 1,
      });
    }
  }, [activeOrg]);

  const onClickAdd = () => {
    router.push(`/${path}/new/`);
    setIsNewRecord(true);
    setRecord(null);
  };

  const onSelectAgent = ({ key }: { key: string }) => {
    const agent = apiData?.find((agent) => agent[idKey] === key);
    if (!agent) return;
    setRecord(agent);
    setIsNewRecord(false);
    const activeTab = params?.get('tab') || null;
    const routeUrl =
      activeTab && TAB_KEYS.includes(activeTab)
        ? `/${path}/${key}?tab=${activeTab}`
        : `/${path}/${key}`;
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
      search: value,
      page_size: pageLimit,
      page: 1,
    });
  };

  const getMenuItems = () => {
    return apiData?.map((item) => ({
      key: item[idKey],
      label: item.name,
      icon: <RiRobot2Line fontSize={18} />,
    }));
  };

  return (
    <AppSidebar
      title={title}
      items={getMenuItems()}
      loading={loading && !isLoadingMore}
      selectedKeys={[String(record?.[idKey] || '')]}
      onClickAdd={onClickAdd}
      onSelectMenu={onSelectAgent}
      initialLoader={<SidebarAgentList />}
      onEndReached={onEndReached}
      isLoadingMore={isLoadingMore}
      onSearch={onSearch}
    />
  );
};

export default Sidebar;
