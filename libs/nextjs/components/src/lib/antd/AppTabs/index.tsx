'use client';
import {useEffect, useMemo, useState} from 'react';
import {useRouter, useSearchParams} from 'next/navigation';
import {StyledTabs} from './styled';
import {TabsProps} from 'antd';

type AppTabsProps = TabsProps & {
  routePath?: string;
};

const AppTabs: React.FC<AppTabsProps> = ({
                                           size = 'middle',
                                           activeKey,
                                           items,
                                           onChange,
                                           routePath,
                                           ...restProps
                                         }) => {
  const [activeTab, setActiveTab] = useState<string | undefined>(
    activeKey ? String(activeKey) : undefined,
  );
  const query = useSearchParams();
  const router = useRouter();
  const itemsList = items ?? [];
  const allTabKeys = useMemo(
    () => itemsList.map((item) => String(item?.key ?? '')),
    [itemsList],
  );

  useEffect(() => {
    const selectedTab =
      query?.get('tab') || (activeKey ? String(activeKey) : undefined);
    if (selectedTab && allTabKeys.includes(selectedTab)) {
      setActiveTab(selectedTab);
    } else {
      setActiveTab(allTabKeys[0]);
    }
  }, [activeKey, allTabKeys, query]);

  const onChangeTab = (key: string) => {
    setActiveTab(key);
    if (routePath) {
      router.push(`${routePath}?tab=${key}`);
    }
    onChange?.(key);
  };

  return (
    <StyledTabs
      size={size}
      items={itemsList}
      activeKey={activeTab}
      onChange={onChangeTab}
      {...restProps}
    />
  );
};

export default AppTabs;
