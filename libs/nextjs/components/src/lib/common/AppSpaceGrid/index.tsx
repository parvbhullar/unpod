'use client';
import React, {useEffect, useMemo} from 'react';
import {useRouter} from 'next/navigation';
import {useAuthActionsContext, useAuthContext, useFetchDataApi,} from '@unpod/providers';
import GridItem from './GridItem';
import {StyledRoot} from './index.styled';
import AppGrid from '../AppGrid';
import {KnowledgeBaseCardSkeleton} from '@unpod/skeleton';
import {SPACE_VISIBLE_CONTENT_TYPES} from '@unpod/constants';
import {useIntl} from 'react-intl';
import type {Spaces} from '@unpod/constants/types';

type AppSpaceGridProps = {
  type?: 'space' | 'kb';
  domainHandle?: string;
};

const AppSpaceGrid: React.FC<AppSpaceGridProps> = ({type = 'kb'}) => {
  const router = useRouter();
  const {isAuthenticated, activeOrg, user} = useAuthContext();
  const {updateAuthUser} = useAuthActionsContext();
  const {formatMessage} = useIntl();

  const [{apiData, loading}, {reCallAPI, setData}] = useFetchDataApi<
    Spaces[]
  >(
    `spaces/`,
    [],
    {
      space_type: type === 'space' ? 'general' : 'knowledge_base',
      case: 'all',
    },
    false,
  );


  useEffect(() => {
    if (isAuthenticated && activeOrg) {
      setData([]);
      reCallAPI();
    }
  }, [isAuthenticated, activeOrg]);

  const onCardClick = (data: Spaces) => {
    if (type === 'space') {
      router.push(`/spaces/${data.slug}/`);
      return;
    }

    router.push(`/knowledge-bases/${data.slug}/`);
  };

  const spaces = useMemo(() => {
    if (type === 'space') {
      const data = apiData.filter((space: Spaces) =>
        SPACE_VISIBLE_CONTENT_TYPES.includes(space.content_type ?? ''),
      );
      if (
        data.length > 0 &&
        user &&
        user.active_space?.slug !== data[0]?.slug
      ) {
        updateAuthUser({
          ...user,
          active_space: data[0],
        });
      }
      return data;
    } else {
      return apiData;
    }
  }, [apiData, type, user, updateAuthUser]);

  return (
    <StyledRoot>
      <AppGrid<Spaces>
        itemPadding={24}
        responsive={{
          xs: 1,
          sm: 2,
          md: 3,
          lg: 4,
        }}
        data={spaces}
        loading={loading}
        noDataMessage={
          type === 'space'
            ? formatMessage({id: 'space.noSpacesFound'})
            : formatMessage({id: 'knowledgeBase.noKnowledgeBaseFound'})
        }
        initialLoader={<KnowledgeBaseCardSkeleton/>}
        renderItem={(item, index) => (
          <GridItem
            key={index}
            data={item}
            onCardClick={onCardClick}
            type={type}
            reCallAPI={reCallAPI}
          />
        )}
      />
    </StyledRoot>
  );
};

export default AppSpaceGrid;
