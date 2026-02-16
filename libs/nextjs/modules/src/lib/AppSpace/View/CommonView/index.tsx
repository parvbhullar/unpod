import { Fragment } from 'react';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import { StyledContainer } from '../index.styled';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';
import PageHeader from '../PageHeader';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import GeneralView from '../GeneralView';

const CommonView = ({
  queryRef,
  onDataSaved,
}: {
  queryRef?: any;
  onDataSaved: (data?: any) => void;
}) => {
  const AppSpaceHeaderMenusAny = AppSpaceHeaderMenus as any;
  const AppQueryWindowAny = AppQueryWindow as any;
  return (
    <Fragment>
      <PageHeader
        pageTitle={
          <AppSpaceHeaderMenusAny
            setAddNew={() => null}
            isContentHeader
            // breadcrumb={breadcrumb}
          />
        }
      />
      <AppPageContainer>
        <StyledContainer>
          <AppQueryWindowAny
            ref={queryRef}
            pilotPopover
            onDataSaved={onDataSaved}
          />
        </StyledContainer>

        <GeneralView listingType="list" />
      </AppPageContainer>
    </Fragment>
  );
};

export default CommonView;
