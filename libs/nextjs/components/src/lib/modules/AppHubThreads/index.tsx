import { useEffect } from 'react';

import { useFetchDataApi } from '@unpod/providers';
import type { Thread } from '@unpod/constants/types';
import AppPostGrid from '../AppPostGrid';
import AppPostList from '../AppPostList';
import AppLoadingMore from '../../common/AppLoadingMore';
import AppLoader from '../../common/AppLoader';
import AppEmptyWorkSpace from '../AppEmptyWorkSpace';

type AppHubThreadsProps = {
  currentHub?: { domain_handle?: string; joined?: boolean };
  listingType?: 'grid' | 'list';};

const AppHubThreads = ({ currentHub, listingType }: AppHubThreadsProps) => {
  const [
    { apiData, loading, page, isLoadingMore },
    { setPage, setLoadingMore, updateInitialUrl, setData },
  ] = useFetchDataApi<Thread[]>(
    `threads/organisation-threads/${currentHub?.domain_handle}/`,
    [],
    {},
    false,
  );

  useEffect(() => {
    if (currentHub) {
      if (currentHub?.joined) {
        updateInitialUrl(
          `threads/organisation-threads/${currentHub?.domain_handle}/`,
        );
      }
    }
  }, [currentHub]);

  return apiData?.length ? (
    <div style={{ minHeight: '50vh' }}>
      {listingType === 'grid' ? (
        <AppPostGrid
          loading={loading}
          apiData={apiData}
          page={page}
          isLoadingMore={isLoadingMore}
          setLoadingMore={setLoadingMore}
          setPage={setPage}
          setData={setData}
          pageSize={10}
          containerStyle={undefined}
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

      {isLoadingMore && <AppLoadingMore />}
    </div>
  ) : loading ? (
    <AppLoader />
  ) : (
    <AppEmptyWorkSpace type="org" />
  );
};

export default AppHubThreads;
