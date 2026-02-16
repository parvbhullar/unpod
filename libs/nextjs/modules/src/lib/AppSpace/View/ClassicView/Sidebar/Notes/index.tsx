import { forwardRef, useEffect, useImperativeHandle } from 'react';
import type { Conversation, NotesHandle } from '@unpod/constants/types';
import {
  getDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
  usePaginatedDataApi,
} from '@unpod/providers';
import { POST_TYPE } from '@unpod/constants/AppEnums';
import NoteItem from './NoteItem';
import AppList from '@unpod/components/common/AppList';
import { NotesSkeleton } from '@unpod/skeleton/Notes';
import { useRouter } from 'next/navigation';

type NotesProps = Record<string, never>;

const Notes = forwardRef<NotesHandle, NotesProps>((_props, ref) => {
  const { setActiveNote } = useAppSpaceActionsContext();
  const { activeNote, activeTab, currentSpace } = useAppSpaceContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();
  const spaceToken = currentSpace?.token ?? '';
  const [
    { apiData, loading, isLoadingMore, hasMoreRecord, page },
    { setLoadingMore, setPage, setData, setQueryParams },
  ] = usePaginatedDataApi(`threads/${spaceToken}/`, [], {
    post_type: POST_TYPE.POST,
  }) as unknown as [
    {
      apiData: Conversation[];
      loading: boolean;
      isLoadingMore: boolean;
      hasMoreRecord: boolean;
      page: number;
    },
    {
      setLoadingMore: (value: boolean) => void;
      setPage: (value: number) => void;
      setData: (
        value: Conversation[] | ((prev: Conversation[]) => Conversation[]),
      ) => void;
      setQueryParams: (params: Record<string, unknown>) => void;
    },
  ];

  useEffect(() => {
    if (currentSpace?.token) {
      setQueryParams({
        page: 1,
        post_type: POST_TYPE.POST,
      });
    }
  }, [currentSpace?.token]);

  useEffect(() => {
    if (!activeNote) return;
    const isNoteExist = apiData.find(
      (item) => item.post_id === activeNote.post_id,
    );
    if (isNoteExist)
      setData((prevData) =>
        prevData.map((item) =>
          item.post_id === activeNote.post_id ? activeNote : item,
        ),
      );
    else {
      setData((prevData) => [activeNote, ...prevData]);
    }
  }, [activeNote]);

  const refreshData = () => {
    setData([]);
    setPage(1);
  };

  useImperativeHandle(ref, () => ({
    refreshData: () => {
      refreshData();
    },
  }));

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const onNoteClick = (note: Conversation) => {
    if (!currentSpace?.slug) return;
    router.replace(`/spaces/${currentSpace.slug}/${activeTab}/${note.slug}`);
    getDataApi<Conversation>(
      `threads/${note.slug}/detail/`,
      infoViewActionsContext,
    )
      .then((data) => {
        const response = data;
        if (response.data) setActiveNote(response.data);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <AppList
      style={{
        height: `calc(100vh - 80px)`,
        padding: '4px 8px',
      }}
      data={apiData}
      loading={loading}
      initialLoader={<NotesSkeleton />}
      renderItem={(thread, index) => (
        <NoteItem
          key={index}
          thread={thread}
          activeNote={activeNote}
          onThreadClick={onNoteClick}
        />
      )}
      onEndReached={onEndReached}
      footerProps={{
        loading: isLoadingMore,
        hasMoreRecord: hasMoreRecord,
      }}
    />
  );
});

export default Notes;
