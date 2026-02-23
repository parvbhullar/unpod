import {Fragment} from 'react';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import PageHeader from '../../View/PageHeader';
import GeneralView from '../../View/GeneralView';
import {StyledContainer} from '../../View/index.styled';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';

const PublicView = ({
                      onDataSaved,
                      queryRef,
                    }: {
  onDataSaved: (data?: any) => void;
  queryRef?: any;
}) => {

  return (
    <Fragment>
      <PageHeader
        pageTitle={
          <AppSpaceHeaderMenus
            setAddNew={() => null}
            isContentHeader
            // breadcrumb={breadcrumb}
          />
        }
      />
      <AppPageContainer>
        <StyledContainer>
          <AppQueryWindow
            ref={queryRef}
            pilotPopover
            onDataSaved={onDataSaved}
          />
        </StyledContainer>

        <GeneralView listingType="list"/>
      </AppPageContainer>
    </Fragment>
  );
};

export default PublicView;
