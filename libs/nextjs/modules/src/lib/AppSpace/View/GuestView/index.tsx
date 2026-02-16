import { Fragment } from 'react';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import PageHeader from '../../View/PageHeader';
import {
  StyledNoAccessContainer,
  StyledNoAccessText,
} from '../../View/index.styled';
import { useIntl } from 'react-intl';

const GuestView = () => {
  const { formatMessage } = useIntl();
  const AppSpaceHeaderMenusAny = AppSpaceHeaderMenus as any;
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
        <StyledNoAccessContainer>
          <StyledNoAccessText level={2}>
            {formatMessage({ id: 'auth.signInToAccess' })}
          </StyledNoAccessText>
        </StyledNoAccessContainer>
      </AppPageContainer>
    </Fragment>
  );
};

export default GuestView;
