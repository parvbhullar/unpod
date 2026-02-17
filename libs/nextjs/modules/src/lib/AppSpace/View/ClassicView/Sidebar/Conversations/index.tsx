import type { Ref } from 'react';
import { forwardRef, useEffect, useImperativeHandle } from 'react';
import type { Conversation, ConversationsHandle } from '@unpod/constants/types';
import {
  getDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
  usePaginatedDataApi,
} from '@unpod/providers';
import { POST_TYPE } from '@unpod/constants/AppEnums';
import ConversationItem from './ConversationItem';
import AppList from '@unpod/components/common/AppList';
import { ConversationsSkeleton } from '@unpod/skeleton/Conversation';
import { useRouter } from 'next/navigation';

type ConversationThread = Conversation & {
  slug?: string;
  title?: string;
  created?: string;
  content?: string;
  user?: Record<string, unknown>;
  block?: { data?: { content?: string } };
};

type ConversationsProps = Record<string, never>;

const ConversationsComponent = (
  _props: ConversationsProps,
  ref: Ref<ConversationsHandle>,
) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { setActiveConversation } = useAppSpaceActionsContext();
  const { activeConversation, activeTab, currentSpace } = useAppSpaceContext();
  const router = useRouter();

  const [
    { apiData, loading, isLoadingMore, hasMoreRecord, page },
    { setLoadingMore, setPage, setData, setQueryParams },
  ] = usePaginatedDataApi(
    `threads/${currentSpace?.token ?? ''}/`,
    [],
    {
      page_size: 20,
      post_type: `${POST_TYPE.ASK},${POST_TYPE.TASK},${POST_TYPE.QUESTION}`,
    },
    false,
  ) as unknown as [
    {
      apiData: ConversationThread[];
      loading: boolean;
      isLoadingMore: boolean;
      hasMoreRecord: boolean;
      page: number;
    },
    {
      setLoadingMore: (value: boolean) => void;
      setPage: (value: number) => void;
      setData: (
        value:
          | ConversationThread[]
          | ((prev: ConversationThread[]) => ConversationThread[]),
      ) => void;
      setQueryParams: (params: Record<string, unknown>) => void;
    },
  ];

  useEffect(() => {
    if (currentSpace?.token) {
      // newConvRef.current?.resetContext();//TODO: enable this when suggestions are needed XXXXXXXX
      setQueryParams({
        page: 1,
        page_size: 20,
        post_type: `${POST_TYPE.ASK},${POST_TYPE.TASK},${POST_TYPE.QUESTION}`,
      });
    }
  }, [currentSpace?.token]);

  useImperativeHandle(
    ref,
    () => ({
      refreshData: () => {
        setData([]);
        setPage(1);
      },
      addConversation: (newConversation: ConversationThread) => {
        // Add new conversation to the top of the list
        setData((prevData) => [newConversation, ...prevData]);
      },
    }),
    [setData, setPage],
  );

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const onConversationClick = (thread: ConversationThread) => {
    if (!currentSpace?.slug || !thread.slug) return;
    router.replace(`/spaces/${currentSpace.slug}/${activeTab}/${thread.slug}`);
    getDataApi<Conversation>(
      `threads/${thread.slug}/detail/`,
      infoViewActionsContext,
    )
      .then((data) => {
        // setActiveNote(null);
        // setActiveDocument(null);
        const response = data;
        if (response.data) setActiveConversation(response.data);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <AppList
      style={{
        height: 'calc(100vh - 80px)',
        padding: '4px 8px',
      }}
      data={apiData}
      loading={loading}
      initialLoader={<ConversationsSkeleton />}
      renderItem={(item, index) => (
        <ConversationItem
          key={index}
          thread={item as ConversationThread}
          activeConversation={activeConversation as ConversationThread | null}
          onThreadClick={onConversationClick}
        />
      )}
      onEndReached={onEndReached}
      footerProps={{
        loading: isLoadingMore,
        hasMoreRecord: hasMoreRecord,
      }}
    />
  );
};

const Conversations = forwardRef<ConversationsHandle, ConversationsProps>(
  ConversationsComponent,
);
Conversations.displayName = 'Conversations';

export default Conversations;
