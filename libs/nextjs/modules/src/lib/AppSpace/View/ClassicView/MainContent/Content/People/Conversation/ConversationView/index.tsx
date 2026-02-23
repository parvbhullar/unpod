import {useCallback, useEffect, useState} from 'react';
import {Button} from 'antd';
import {MdRefresh} from 'react-icons/md';
import {
  deleteDataApi,
  getDataApi,
  putDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {tablePageSize} from '@unpod/constants';
import {getRandomColor} from '@unpod/helpers/StringHelper';
import ReplyItem from '@unpod/components/modules/AppPostReplies/ReplyItem';
import AppConfirmModal from '@unpod/components/antd/AppConfirmModal';
import {StyledMoreContainer} from './index.styled';
import AppList from '@unpod/components/common/AppList';
import type {Conversation} from '@unpod/constants/types';

type ReplyUser = {
  user_token?: string;
  profile_color?: string;
  [key: string]: unknown;
};

type ReplyData = {
  content?: string;
  [key: string]: unknown;
};

type ReplyItemData = {
  block_id?: string;
  block_type?: string;
  reaction_count?: number | string;
  replies?: ReplyItemData[];
  user: ReplyUser;
  data: ReplyData;
  context?: string;
  [key: string]: unknown;
};

type ConversationViewProps = {
  conversation: Conversation;
};

const ConversationView = ({conversation}: ConversationViewProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {activeOrg} = useAuthContext();
  const [selectedBlock, setSelectedBlock] = useState<ReplyItemData | null>(
    null,
  );
  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<ReplyItemData[]>([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMoreRecords, setHasMoreRecords] = useState(false);
  const [replyParent, setReplyParent] = useState<ReplyItemData | null>(null);

  const [{apiData, loading}, {setData, setQueryParams}] = useGetDataApi(
    `conversation/${conversation.post_id}/messages/`,
    {data: []},
    {
      domain: activeOrg?.domain_handle,
      page: 1,
      page_size: tablePageSize,
    },
    true,
  ) as unknown as [
    { apiData?: { data?: ReplyItemData[] }; loading: boolean },
    {
      setData: (data: { data: ReplyItemData[] }) => void;
      setQueryParams: (params: Record<string, unknown>) => void;
    },
  ];

  useEffect(() => {
    const data = apiData?.data ?? [];
    if (data.length > 0) {
      setHasMoreRecords(data.length === tablePageSize);

      let context = '';

      setItems(
        data
          .filter((item) => item.block_type !== 'sys_msg')
          .map((item) => {
            if (item.user?.user_token) {
              context = item.data?.content || '';
            }

            return {
              ...item,
              user: {
                ...item.user,
                profile_color: item.user?.profile_color || getRandomColor(),
              },
              context,
            };
          }),
      );
    } else {
      setHasMoreRecords(false);
    }
  }, [apiData?.data]);

  useEffect(() => {
    setPage(1);
    setItems([]);
    setData({data: []});
    setQueryParams({
      domain: activeOrg?.domain_handle,
      page: 1,
      page_size: tablePageSize,
    });
  }, [conversation.post_id]);

  const onReplyClick = useCallback((reply: ReplyItemData) => {
    setReplyParent(reply);
  }, []);

  const onClapClick = useCallback(
    (
      reply: ReplyItemData,
      reactionCount: number,
      isSubReply = false,
      parentReply: ReplyItemData | null = null,
    ) => {
      putDataApi<ReplyItemData[]>(
        `threads/${reply.block_id}/reaction/?post_type=block`,
        infoViewActionsContext,
        {
          reaction_type: 'clap',
          reaction_count: reactionCount,
        },
        true,
      )
        .then((res) => {
          const response = res as {
            data?: { reaction?: unknown };
            message?: string;
          };
          if (response.data?.reaction) {
            if (response.message)
              infoViewActionsContext.showMessage(response.message);

            setItems((prevState) => {
              const selectedReply = {...reply};

              if (isSubReply && parentReply && replyParent) {
                const selectedParentReply = {...parentReply};
                selectedReply.reaction_count =
                  Number(selectedReply.reaction_count || 0) + reactionCount;

                selectedParentReply.replies = (parentReply.replies ?? []).map(
                  (item) =>
                    item.block_id === selectedReply.block_id
                      ? selectedReply
                      : item,
                );

                return prevState.map((item) =>
                  item.block_id === replyParent.block_id
                    ? selectedParentReply
                    : item,
                );
              } else {
                selectedReply.reaction_count =
                  Number(selectedReply.reaction_count || 0) + reactionCount;
                return prevState.map((item) =>
                  item.block_id === selectedReply.block_id
                    ? selectedReply
                    : item,
                );
              }
            });
          }
        })
        .catch((error) => {
          infoViewActionsContext.showError(error.message);
        });
    },
    [replyParent],
  );

  const loadOlderMessages = () => {
    setLoadingMore(true);
    getDataApi<ReplyItemData[]>(
      `conversation/${conversation.post_id}/messages/`,
      infoViewActionsContext,
      {
        domain: activeOrg?.domain_handle,
        page: page + 1,
        page_size: tablePageSize,
      },
    )
      .then((data) => {
        const response = data;
        const responseData = response.data ?? [];
        setLoadingMore(false);
        if (responseData.length) {
          if (responseData.length === tablePageSize) {
            setHasMoreRecords(true);
            setPage(page + 1);
          } else {
            setHasMoreRecords(false);
          }
          let context = conversation.title;
          setItems((prevState) => [
            ...responseData
              .filter((item) => item.block_type !== 'sys_msg')
              .map((item) => {
                if (item.user?.user_token) {
                  context = item.data?.content || '';
                }

                return {
                  ...item,
                  user: {
                    ...item.user,
                    profile_color: item.user?.profile_color || getRandomColor(),
                  },
                  context,
                };
              }),
            ...prevState,
          ]);
        } else {
          setHasMoreRecords(false);
          infoViewActionsContext.showMessage(
            response.message || 'No more data',
          );
        }
      })
      .catch((error) => {
        setLoadingMore(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  const onMenuClick = useCallback((key: string, block: ReplyItemData) => {
    setSelectedBlock(block);

    if (key === 'delete') {
      setDeleteOpen(true);
    }
  }, []);

  const onBlockDelete = () => {
    if (selectedBlock?.block_id) {
      deleteDataApi<unknown>(
        `threads/${selectedBlock.block_id}/action/`,
        infoViewActionsContext,
        {post_type: 'block'},
        true,
      )
        .then((data) => {
          const response = data;
          if (response.message)
            infoViewActionsContext.showMessage(response.message);
          setItems((prevState) =>
            prevState.filter(
              (item) => item.block_id !== selectedBlock.block_id,
            ),
          );

          setDeleteOpen(false);
          setSelectedBlock(null);
        })
        .catch((error) => {
          infoViewActionsContext.showError(error.message);
        });
    }
  };

  return (
    <>
      <AppList
        style={{
          height: 'calc(100vh - 130px)',
          maxWidth: '800px',
        }}
        data={items}
        extra={
          hasMoreRecords && (
            <StyledMoreContainer>
              <Button
                type="primary"
                shape="round"
                size="small"
                onClick={loadOlderMessages}
                loading={loadingMore}
                ghost
                icon={<MdRefresh fontSize={16}/>}
              >
                Load Older Messages
              </Button>
            </StyledMoreContainer>
          )
        }
        loading={loading}
        renderItem={(replyItem) => (
          <ReplyItem
            key={replyItem.block_id}
            reply={replyItem}
            replyParent={replyParent}
            onReplyClick={onReplyClick}
            onClapClick={onClapClick}
            onMenuClick={onMenuClick}
            hideReply={true}
            hideDelete={true}
          />
        )}
      />

      <AppConfirmModal
        open={isDeleteOpen}
        onOk={onBlockDelete}
        message="Are you sure you want to delete?"
        onCancel={() => setDeleteOpen(false)}
      />
    </>
  );
};

export default ConversationView;
