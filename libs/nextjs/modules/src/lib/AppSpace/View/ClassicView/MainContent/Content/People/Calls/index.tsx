'use client';
import {useState} from 'react';
import AppList from '@unpod/components/common/AppList';
import {useAppSpaceActionsContext, useAppSpaceContext, useAuthContext, useGetDataApi,} from '@unpod/providers';
import CallItem from './CallItem';
import type {Call} from '@unpod/constants/types';
import {AppDrawer} from '@unpod/components/antd';
import CallLogs from '../../Calls';
import CallHeader from '../../../Header/CallHeader';
import {IoMdClose} from 'react-icons/io';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import {StyledHeaderTitle} from './index.styled';
import {useMediaQuery} from 'react-responsive';
import {TabWidthQuery} from '@unpod/constants';

const Calls = () => {
  const {activeOrg} = useAuthContext();
  const {currentSpace, activeDocument, activeCall} = useAppSpaceContext();
  const {setActiveCall} = useAppSpaceActionsContext();
  const [showDrawer, setShowDrawer] = useState(false);
  const isTablet = useMediaQuery(TabWidthQuery);

  const [{apiData, loading}] = useGetDataApi(
    `knowledge_base/${currentSpace?.token}/connector-doc-data/${activeDocument?.document_id}/tasks/`,
    {data: []},
    {
      domain: activeOrg?.domain_handle,
      page_size: 20,
      page: 1,
    },
  ) as unknown as [{ apiData?: { data?: Call[] }; loading: boolean }];

  const onCallClick = (data: Call) => {
    setActiveCall(data);
    setShowDrawer(true);
  };

  const onClose = () => {
    setShowDrawer(false);
    setActiveCall(null);
  };

  return (
    <>
      <AppList
        style={{height: 'calc(100vh - 135px)', padding: '24px 14px'}}
        data={apiData?.data ?? []}
        loading={loading}
        itemSpacing={16}
        renderItem={(data, index) => (
          <CallItem
            key={`index-${index}`}
            data={data as Call}
            onCallClick={onCallClick}
          />
        )}
      />

      <AppDrawer
        rootClassName="my-custom-drawer"
        padding="0"
        open={showDrawer}
        onClose={onClose}
        width={isTablet ? '100%' : 'calc(100% - 405px)'}
      >
        {activeCall && (
          <>
            <StyledHeaderTitle>
              <CallHeader/>
              <AppHeaderButton
                shape="circle"
                icon={<IoMdClose size={16}/>}
                onClick={onClose}
              />
            </StyledHeaderTitle>
            <CallLogs/>
          </>
        )}
      </AppDrawer>
    </>
  );
};

export default Calls;
