import { Fragment } from 'react';
import PageHeader from '../../View/PageHeader';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import RequestWorkSpace from './RequestWorkSpace';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';

const RequestView = () => {
  const { currentSpace } = useAppSpaceContext();
  const { setCurrentSpace } = useAppSpaceActionsContext();
  const AppSpaceHeaderMenusAny = AppSpaceHeaderMenus as any;

  return (
    <Fragment>
      <PageHeader
        pageTitle={
          <AppSpaceHeaderMenusAny setAddNew={() => null} isContentHeader />
        }
      />
      <AppPageContainer
        style={{ height: 'calc(100vh - 74px)', borderRadius: 0 }}
      >
        <RequestWorkSpace
          currentData={currentSpace}
          setCurrentData={setCurrentSpace}
        />
      </AppPageContainer>
    </Fragment>
  );
};

export default RequestView;
