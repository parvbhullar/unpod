'use client';

import type {
  AppOrgContextProviderProps,
  NotificationData,
  OrgActionsContextType,
  Organization,
  OrgContextType,
  OrgUser,
  Spaces,
} from '@unpod/constants/types';

import React, {createContext, useContext, useEffect, useMemo, useState,} from 'react';

import {setOrgHeader} from '@unpod/services';

import {
  getDataApi,
  useAuthActionsContext,
  useAuthContext,
  useFetchDataApi,
  useInfoViewActionsContext,
} from '../../../index';

const OrgActionsContext = createContext<OrgActionsContextType | undefined>(
  undefined,
);
const OrgContext = createContext<OrgContextType | undefined>(undefined);

export const useOrgContext = (): OrgContextType => {
  const context = useContext(OrgContext);
  if (!context) {
    throw new Error('useOrgContext must be used within AppOrgContextProvider');
  }
  return context;
};

export const useOrgActionContext = (): OrgActionsContextType => {
  const context = useContext(OrgActionsContext);
  if (!context) {
    throw new Error(
      'useOrgActionContext must be used within AppOrgContextProvider',
    );
  }
  return context;
};

export const AppOrgContextProvider: React.FC<AppOrgContextProviderProps> = ({
                                                                              children,
                                                                            }) => {
  const {activeOrg, user} = useAuthContext();
  const {setActiveOrg} = useAuthActionsContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [notificationData, setNotificationData] = useState<NotificationData>(
    {},
  );

  const [activeSpace, setActiveSpace] = useState<Spaces>(
    (user?.active_space as Spaces) || {slug: ''},
  );

  const [{apiData: orgUsers}, {updateInitialUrl}] = useFetchDataApi(
    ``,
    [],
    {},
    false,
  );

  useEffect(() => {
    if (
      notificationData?.object_type === 'organization' &&
      notificationData?.event_data?.domain_handle === activeOrg?.domain_handle
    ) {
      getDataApi<Organization>(
        `organization/detail/${activeOrg?.domain_handle}/`,
        infoViewActionsContext,
        {},
      ).then((response) => {
        setActiveOrg(response.data);
      });
    }
  }, [
    notificationData,
    activeOrg?.domain_handle,
    infoViewActionsContext,
    setActiveOrg,
  ]);

  useEffect(() => {
    if (activeOrg?.domain_handle) {
      setOrgHeader(activeOrg?.domain_handle);
      if (activeOrg?.joined)
        updateInitialUrl(`organization/user-list/${activeOrg?.domain_handle}/`);
    }
  }, [activeOrg?.domain_handle, activeOrg?.joined, updateInitialUrl]);

  const actions = useMemo<OrgActionsContextType>(() => {
    return {
      setActiveSpace,
      setNotificationData,
    };
  }, [setActiveSpace, setNotificationData]);

  const values = useMemo<OrgContextType>(() => {
    return {
      activeSpace,
      orgUsers: (orgUsers as OrgUser[]) || [],
      notificationData,
    };
  }, [activeSpace, orgUsers, notificationData]);

  return (
    <OrgActionsContext.Provider value={actions}>
      <OrgContext.Provider value={values}>{children}</OrgContext.Provider>
    </OrgActionsContext.Provider>
  );
};

export default AppOrgContextProvider;
