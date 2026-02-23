'use client';

import {Fragment, useState} from 'react';
import AppPageHeader, {AppHeaderButton,} from '@unpod/components/common/AppPageHeader';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppSpaceGrid from '@unpod/components/common/AppSpaceGrid';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import {StyledContainer} from './index.styled';
import {FiPlus} from 'react-icons/fi';
import {useIntl} from 'react-intl';

const AppSpaceRoot = () => {
  const [addNew, setAddNew] = useState<boolean>(false);
  const {formatMessage} = useIntl();

  return (
    <Fragment>
      <AppPageHeader
        hideToggleBtn
        hideAuthBtn
        isListingPage={false}
        pageTitle={
          <AppSpaceHeaderMenus addNew={addNew} setAddNew={setAddNew}/>
        }
        rightOptions={
          <AppHeaderButton
            type="primary"
            shape="round"
            icon={<FiPlus/>}
            onClick={() => setAddNew(true)}
          >
            {formatMessage({id: 'common.add'})}
          </AppHeaderButton>
        }
      />

      <AppPageContainer>
        <StyledContainer>
          <AppSpaceGrid type={'space'}/>
        </StyledContainer>
      </AppPageContainer>
    </Fragment>
  );
};

export default AppSpaceRoot;
