import { Fragment, type ReactNode } from 'react';
import { Typography } from 'antd';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';
import AppPostGrid from '@unpod/components/modules/AppPostGrid';
import AppPostList from '@unpod/components/modules/AppPostList';
import AppLoader from '@unpod/components/common/AppLoader';
import { useAppContext, useFetchDataApi } from '@unpod/providers';
import { StyledContainer } from './index.styled';
import AppPageHeader from '@unpod/components/common/AppPageHeader';
import AppEmptyWorkSpace from '@unpod/components/modules/AppEmptyWorkSpace';
import { useIntl } from 'react-intl';

const { Title } = Typography;

type NewThreadProps = {
  pageTitle?: ReactNode;
};

const NewThread = ({ pageTitle }: NewThreadProps) => {
  const { listingType } = useAppContext();
  const { formatMessage } = useIntl();

  const [
    { apiData, loading, page, isLoadingMore },
    { setPage, setLoadingMore },
  ] = useFetchDataApi(`threads/explore/trending/`, [], {});

  return (
    <Fragment>
      <AppPageHeader pageTitle={pageTitle} hideToggleBtn isListingPage />

      <AppPageContainer>
        <StyledContainer>
          <AppQueryWindow {...({ pilotPopover: true } as any)} />
        </StyledContainer>

        <Title level={2} className="text-center">
          {formatMessage({ id: 'common.trending' })}
        </Title>

        {apiData?.length ? (
          listingType === 'grid' ? (
            <AppPostGrid
              loading={loading}
              apiData={apiData}
              page={page}
              isLoadingMore={isLoadingMore}
              setLoadingMore={setLoadingMore}
              setPage={setPage}
              maxColumns={4}
            />
          ) : (
            <AppPostList
              loading={loading}
              apiData={apiData}
              page={page}
              isLoadingMore={isLoadingMore}
              setLoadingMore={setLoadingMore}
              setPage={setPage}
            />
          )
        ) : loading ? (
          <AppLoader />
        ) : (
          <AppEmptyWorkSpace />
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default NewThread;
