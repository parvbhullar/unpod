'use client';
import React, { Fragment, useEffect, useState } from 'react';
import { MdOutlineGroup } from 'react-icons/md';
import { useAppContext, useFetchDataApi } from '@unpod/providers';
import AppPostGrid from '@unpod/components/modules/AppPostGrid';
import AppPostList from '@unpod/components/modules/AppPostList';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppPageHeader from '@unpod/components/common/AppPageHeader';
import AppGlobalSearch from '@unpod/components/common/AppGlobalSearch';
import { StyledContainer } from './index.styled';
import AppEmptyWorkSpace from '@unpod/components/modules/AppEmptyWorkSpace';
import { SharedWithMeSkeleton } from '@unpod/skeleton';

type SharedWithMeProps = {
  pageTitle?: React.ReactNode;
};

const SharedWithMe: React.FC<SharedWithMeProps> = ({ pageTitle }) => {
  const { listingType } = useAppContext();

  const [globalSearch, setGlobalSearch] = useState('');

  const [
    { apiData, loading, page, isLoadingMore },
    { setPage, setLoadingMore, setQueryParams },
  ] = useFetchDataApi(`threads/shared/me/`, [], {});

  useEffect(() => {
    if (globalSearch !== '') {
      setQueryParams({
        search: globalSearch,
      });
    }
  }, [globalSearch]);

  return (
    <Fragment>
      <AppPageHeader
        hideToggleBtn
        pageTitle={pageTitle}
        titleIcon={<MdOutlineGroup fontSize={21} />}
        centerOptions={<AppGlobalSearch setGlobalSearch={setGlobalSearch} />}
        isListingPage
      />

      <AppPageContainer>
        {apiData?.length ? (
          <StyledContainer>
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
              <SharedWithMeSkeleton />
            ) : (
              <AppEmptyWorkSpace />
            )}
          </StyledContainer>
        ) : (
          <SharedWithMeSkeleton />
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default SharedWithMe;
