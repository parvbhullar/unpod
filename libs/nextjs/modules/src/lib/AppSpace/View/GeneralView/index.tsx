import { useEffect } from 'react';
import { useAppSpaceContext, useFetchDataApi } from '@unpod/providers';
import AppEmptyWorkSpace from '@unpod/components/modules/AppEmptyWorkSpace';
import AppLoader from '@unpod/components/common/AppLoader';
import AppPostGrid from '@unpod/components/modules/AppPostGrid';
import AppPostList from '@unpod/components/modules/AppPostList';
import AppLoadingMore from '@unpod/components/common/AppLoadingMore';
import type { Thread } from '@unpod/constants/types';

const GeneralView = ({ listingType }: { listingType: any }) => {
  const { currentSpace } = useAppSpaceContext();
  const [
    { apiData, loading, page, isLoadingMore },
    { setData, setPage, setLoadingMore, updateInitialUrl },
  ] = useFetchDataApi<Thread[]>(
    `threads/${currentSpace?.token}/`,
    [],
    {},
    false,
  );

  useEffect(() => {
    if (currentSpace?.token) {
      setData([]);
      setPage(1);
      updateInitialUrl(`threads/${currentSpace?.token}/`);
    }
  }, [currentSpace?.token]);

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
    <AppEmptyWorkSpace />
  );
};

export default GeneralView;
