'use client';
import React, {useMemo, useState} from 'react';
import {StyledRoot, StyledTabsWrapper} from './index.styled';
import {useAppSpaceContext} from '@unpod/providers';
import {AppTabs} from '@unpod/components/antd';
import {getTabItems} from './constants';
import LandingView from './LandingView';
import {useIntl} from 'react-intl';

const CallLogs = () => {
  const {activeCall} = useAppSpaceContext();
  const [activeTab, setActiveTab] = useState('overview');
  const {formatMessage} = useIntl();

  // Memoize tab items to prevent recreating components on every render
  const tabItems = useMemo(
    () => getTabItems(activeTab, formatMessage),
    [activeTab],
  );

  if (!activeCall) {
    return <LandingView/>;
  }

  return (
    <StyledRoot>
      <StyledTabsWrapper>
        <AppTabs
          activeKey={activeTab}
          items={tabItems}
          onChange={setActiveTab}
        />
      </StyledTabsWrapper>
    </StyledRoot>
  );
};

// Memoize component to only re-render when activeCall changes
export default React.memo(CallLogs, () => {
  // Since this component has no props, it will only re-render when context forces it
  // The useMemo inside will prevent tab recreation
  return true; // Always skip re-render from parent, rely on context changes only
});
