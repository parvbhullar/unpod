'use client';

import React from 'react';
import { useAuthContext } from '@unpod/providers';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import CreateOrg from '../../auth/CreateOrg';
import PageHeader from './PageHeader';

import { StyledSettingContainer } from './index.styled';
import AppLoader from '@unpod/components/common/AppLoader';

const Settings = () => {
  const { activeOrg } = useAuthContext();

  return activeOrg ? (
    <React.Fragment>
      <PageHeader pageTitle={activeOrg?.name} />
      <AppPageContainer>
        <StyledSettingContainer>
          <CreateOrg org={activeOrg} />
        </StyledSettingContainer>
      </AppPageContainer>
    </React.Fragment>
  ) : (
    <AppLoader />
  );
};

export default Settings;
