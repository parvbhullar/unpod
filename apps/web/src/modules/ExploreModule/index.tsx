import React, { useEffect, useState } from 'react';
import { useAppContext, useFetchDataApi } from '@unpod/providers';
import AppPostGrid from '@unpod/components/modules/AppPostGrid';
import AppPostList from '@unpod/components/modules/AppPostList';
import AppLoader from '@unpod/components/common/AppLoader';
import AppEmptyWorkSpace from '@unpod/components/modules/AppEmptyWorkSpace';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppGlobalSearch from '@unpod/components/common/AppGlobalSearch';
import AppPageHeader from '@unpod/components/common/AppPageHeader';

type ExploreModuleProps = {
  pageTitle?: React.ReactNode;
};

const ExploreModule: React.FC<ExploreModuleProps> = ({ pageTitle }) => {
  const { listingType } = useAppContext();

  const [globalSearch, setGlobalSearch] = useState('');

  const [
    { apiData, loading, page, isLoadingMore },
    { setPage, setLoadingMore, setQueryParams },
  ] = useFetchDataApi(`threads/explore/trending/`, [], {});

  useEffect(() => {
    if (globalSearch !== '') {
      setQueryParams({
        search: globalSearch,
      });
    }
  }, [globalSearch]);

  return (
    <React.Fragment>
      <AppPageHeader
        hideToggleBtn
        pageTitle={pageTitle}
        leftOptions={<AppGlobalSearch setGlobalSearch={setGlobalSearch} />}
        isListingPage
      />

      <AppPageContainer>
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
    </React.Fragment>
  );
};

export default ExploreModule;
