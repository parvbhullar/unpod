'use client';

import { Fragment, useEffect, useState } from 'react';
import { Typography } from 'antd';
import AppPageHeader from '@unpod/components/common/AppPageHeader';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';
import AppPostGrid from '@unpod/components/modules/AppPostGrid';
import AppPostList from '@unpod/components/modules/AppPostList';
import AppLoader from '@unpod/components/common/AppLoader';
import AppEmptyWorkSpace from '@unpod/components/modules/AppEmptyWorkSpace';
import {
  useAppContext,
  useAuthContext,
  useFetchDataApi,
} from '@unpod/providers';
import { StyledContainer, StyledInfoContainer } from './index.styled';
import { NewThreadSkeleton } from '@unpod/skeleton';

const { Title } = Typography;

const NewThread = () => {
  const { user } = useAuthContext();
  const { listingType } = useAppContext();
  const [isScrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      const scrollPos = window.scrollY;
      setScrolled(scrollPos > 50);
    };
    window.addEventListener('scroll', onScroll);

    return () => {
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  const [
    { apiData, loading, page, isLoadingMore },
    { setPage, setLoadingMore },
  ] = useFetchDataApi(`threads/explore/trending/`, [], {});

  return (
    <Fragment>
      <AppPageHeader hideToggleBtn isListingPage />
      <AppPageContainer>
        {user ? (
          <Fragment>
            <StyledContainer $isScrolled={isScrolled}>
              <StyledInfoContainer>
                <Title level={2}>
                  {user ? `Hello, ${user.first_name}` : 'Welcome Guest'}
                </Title>

                <Title level={3} type="secondary">
                  What are you looking for today?
                </Title>
              </StyledInfoContainer>

              <AppQueryWindow pilotPopover />
            </StyledContainer>
            <Title level={2} className="text-center">
              Trending
            </Title>
          </Fragment>
        ) : (
          <NewThreadSkeleton />
        )}

        {apiData?.length ? (
          <div style={{ minHeight: '50vh' }}>
            {listingType === 'grid' ? (
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
            )}
          </div>
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
