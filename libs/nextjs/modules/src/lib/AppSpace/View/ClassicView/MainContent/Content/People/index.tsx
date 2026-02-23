'use client';
import {useMemo, useState} from 'react';
import PeopleOverview from './Overview';
import Calls from './Calls';
import {AppTabs} from '@unpod/components/antd';
import {StyledRoot, StyledTabsWrapper} from '../Calls/index.styled';
import type {IntlShape} from 'react-intl';
import {useIntl} from 'react-intl';

type TabKey = 'overview' | 'call';

export const getTabItems = (
  activeTab: TabKey,
  formatMessage: IntlShape['formatMessage'],
) => {
  return [
    {
      key: 'overview',
      label: formatMessage({id: 'tab.overview'}),
      children: activeTab === 'overview' && <PeopleOverview/>,
    },
    {
      key: 'call',
      label: formatMessage({id: 'tab.calls'}),
      children: activeTab === 'call' && <Calls/>,
    },
    /*{
      key: 'tasks',
      label: 'Tasks',
      children: <Conversations />,
    },*/
  ];
};
const People = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const {formatMessage} = useIntl();
  const tabItems = useMemo(
    () => getTabItems(activeTab, formatMessage),
    [activeTab],
  );
  const onTabChange = (key: string) => setActiveTab(key as TabKey);

  return (
    <StyledRoot>
      <StyledTabsWrapper>
        <AppTabs
          activeKey={activeTab}
          items={tabItems}
          onChange={onTabChange}
        />
      </StyledTabsWrapper>
    </StyledRoot>
  );
};

export default People;
