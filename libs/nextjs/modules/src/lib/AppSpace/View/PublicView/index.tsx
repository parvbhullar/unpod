import { Fragment } from 'react';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import PageHeader from '../../View/PageHeader';
import GeneralView from '../../View/GeneralView';
import { StyledContainer } from '../../View/index.styled';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';

const PublicView = ({
  onDataSaved,
  queryRef,
}: {
  onDataSaved: (data?: any) => void;
  queryRef?: any;
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

export default PublicView;
