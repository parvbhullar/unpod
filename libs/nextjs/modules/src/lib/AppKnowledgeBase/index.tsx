'use client';
import { Fragment, useState } from 'react';
import AppPageHeader, {
  AppHeaderButton,
} from '@unpod/components/common/AppPageHeader';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppSpaceGrid from '@unpod/components/common/AppSpaceGrid';
import HeaderDropdown from './View/HeaderDropdown';
import { StyledContainer, StyledRoot } from './index.styled';
import { FiPlus } from 'react-icons/fi';
import { useIntl } from 'react-intl';

const AppKnowledgeBaseRoot = () => {
  const [addNew, setAddNew] = useState(false);
  const [currentKb, setCurrentKb] = useState<any>(null);
  const { formatMessage } = useIntl();

  return (
    <Fragment>
      <StyledRoot>
        <AppPageHeader
          hideToggleBtn
          hideAuthBtn
          isListingPage={false}
          pageTitle={
            <HeaderDropdown
              pageTitle={formatMessage({ id: 'knowledgeBase.pageTitle' })}
              currentKb={currentKb}
              setCurrentKb={setCurrentKb}
              addNew={addNew}
              setAddNew={setAddNew}
            />
          }
          rightOptions={
            <AppHeaderButton
              type="primary"
              shape="round"
              onClick={() => setAddNew(true)}
              icon={<FiPlus />}
            >
              {formatMessage({ id: 'common.add' })}
            </AppHeaderButton>
          }
        />

        <AppPageContainer>
          <StyledContainer>
            <AppSpaceGrid type="kb" />
          </StyledContainer>
        </AppPageContainer>
      </StyledRoot>
    </Fragment>
  );
};

export default AppKnowledgeBaseRoot;
