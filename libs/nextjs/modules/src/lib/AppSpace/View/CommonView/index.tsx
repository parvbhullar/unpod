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

        <GeneralView listingType="list" />
      </AppPageContainer>
    </Fragment>
  );
};

export default CommonView;
