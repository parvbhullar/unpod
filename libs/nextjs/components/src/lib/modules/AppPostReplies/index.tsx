import type { CSSProperties, Ref } from 'react';
import {
  Fragment,
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';

import { Button, Row, Spin, Typography } from 'antd';
import { MdRefresh } from 'react-icons/md';
import { RiArrowDownLine } from 'react-icons/ri';
import clsx from 'clsx';
import {
  deleteDataApi,
  getDataApi,
  putDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { tablePageSize } from '@unpod/constants';
import {
  isScrolledToBottom,
  scrollToPostBottom,
} from '@unpod/helpers/GlobalHelper';
import { getRandomColor } from '@unpod/helpers/StringHelper';
import { POST_TYPE } from '@unpod/constants/AppEnums';
import AppDotFlashing from '../../common/AppDotFlashing';
import ReplyItem from './ReplyItem';
import {
  StyledAppList,
  StyledInnerContainer,
  StyledMoreContainer,
  StyledMsgChat,
  StyledRootContainer,
  StyledScrollBottom,
} from './index.styled';
import AppConfirmModal from '../../antd/AppConfirmModal';
import { useIntl } from 'react-intl';

const ConversationState = {
  IDLE: 'idle',
  LOADING: 'loading',
  STARTING: 'starting',
  ALREADY_STREAMED: 'already_streamed',
};

const { Text } = Typography;

type AppPostRepliesProps = {
  activePost: any;
  lastMessage?: any;
  replyParent?: any;
  setReplyParent?: (value: any) => void;
  actionsStyle?: CSSProperties;
  thinking?: boolean;
  setThinking?: (value: boolean) => void;
  setStreaming?: (value: boolean) => void;
  setDataLoading?: (value: boolean) => void;
  onSaveNote?: (data: any) => void;
  conversationState?: string;
  setConversationState?: (state: string) => void;
  ref?: Ref<any>;};

const AppPostReplies = ({
  activePost,
  lastMessage,
  replyParent,
  setReplyParent,
  actionsStyle,
  thinking,
  setThinking,
  setStreaming,
  setDataLoading,
  onSaveNote,
  conversationState,
  setConversationState,
  ref,
}: AppPostRepliesProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { isLoading, visitorId, isAuthenticated } = useAuthContext();
  const [selectedBlock, setSelectedBlock] = useState<any | null>(null);
  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<any[]>([]);
  const [streamItems, setStreamItems] = useState<any[]>([]);
  const [isReachBottom, setScrolledBottom] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMoreRecords, setHasMoreRecords] = useState(false);
  const [systemMessage, setSystemMessage] = useState<any | null>(null);
  const [noteTitle, setNoteTitle] = useState<string | null>(null);
  const { formatMessage } = useIntl();

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [{ apiData, loading }, { setData, updateInitialUrl, setQueryParams }] =
    (useGetDataApi(
      `conversation/${activePost.post_id}/messages/`,
      { data: [] },
      { page: 1, page_size: tablePageSize },
      false,
    ) as any) || [];

  useEffect(() => {
    if (apiData?.data?.length === tablePageSize) {
      console.log('AppPostReplies apiData Adding scroll listener');
      window.addEventListener(
        'scroll',
        function () {
          const scrollPos = window.scrollY;
          const data = isScrolledToBottom();
          setScrolledBottom(data);

          console.log(
            'AppPostReplies scrollPos setScrolledBottom ',
            scrollPos,
            data,
          );
        },
        true,
      );
      setConversationState?.(ConversationState.LOADING);
    }
    return () => {
      window.removeEventListener('scroll', function () {
        const scrollPos = window.scrollY;
        void scrollPos;
      });
    };
  }, [apiData?.data?.length]);

  useEffect(() => {
    if (activePost.title) {
      const title = activePost.title === 'No Title' ? '' : activePost.title;
      setNoteTitle(
        activePost.post_type === POST_TYPE.ASK
          ? activePost.content || title
          : title || activePost.content,
      );
    }
  }, [activePost.title]);

  useEffect(() => {
    if (!isLoading && visitorId) {
      updateInitialUrl(`conversation/${activePost.post_id}/messages/`, false);
      setPage(1);

      if (isAuthenticated) {
        setQueryParams({ page: 1, page_size: tablePageSize });
      } else {
        setQueryParams({
          page: 1,
          page_size: tablePageSize,
          session_user: visitorId,
        });
      }
    }

    return () => {
      setItems([]);
      setData({ data: [] });
    };
  }, [activePost.post_id, isLoading, isAuthenticated, visitorId]);
  useEffect(() => {
    if (apiData?.data?.length > 0) {
      if (page === 1) {
        setConversationState?.(ConversationState.ALREADY_STREAMED);
      }
      setDataLoading?.(false);
      setHasMoreRecords(apiData.data.length === tablePageSize);

      let context = '';

      setItems(
        apiData.data
          .filter((item: any) => item.block_type !== 'sys_msg')
          .map((item: any) => {
            if (item.user.user_token) {
              context = item.data.content;
            }

            return {
              ...item,
              user: {
                ...item.user,
                profile_color: item.user.profile_color,
              },
              context,
            };
          }),
      );

      setTimeout(() => {
        setScrolledBottom(isScrolledToBottom(0));
      }, 100);
    } else {
      if (
        apiData?.data &&
        page === 1 &&
        conversationState !== ConversationState.ALREADY_STREAMED
      )
        setConversationState?.(ConversationState.STARTING);
      setHasMoreRecords(false);
    }
  }, [apiData?.data]);

  useImperativeHandle(ref, () => {
    return {
      resetSystemMessage() {
        setStreamItems((prevState) => {
          setItems((prevItems) => [...prevItems, ...prevState]);

          return [];
        });
        setSystemMessage(null);
      },
    };
  }, []);

  const onReplyClick = useCallback((reply: any) => {
    setReplyParent?.(reply);
  }, []);

  useEffect(() => {
    if (lastMessage?.data) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }

      const data = JSON.parse(lastMessage?.data);
      // console.log('AppPostReplies lastMessage received', { data });

      // Handle transcription messages from LiveKit
      if (data?.type === 'transcription' && data?.event === 'block') {
        const messageData = {
          block_id: data.block_id,
          thread_id: data.thread_id,
          user_id: data.user_id,
          user: {
            ...data.user,
            profile_color: data.user.profile_color || getRandomColor(),
          },
          block: data.block,
          block_type: data.block_type,
          data: data.data,
          media: data.media || {},
          seq_number: data.seq_number || 1,
          reaction_count: data.reaction_count || 0,
          parent_id: data.parent_id,
          parent: data.parent || {},
          created: data.created,
        };

        // Check if message already exists in items (old messages)
        const existsInItems = items.some(
          (item) => item.block_id === data.block_id,
        );

        // Check if message already exists in streamItems
        const existingIndex = streamItems.findIndex(
          (item) => item.block_id === data.block_id,
        );

        if (existsInItems) {
          // Message already exists in items - update it if needed
          if (data.data.final) {
            setItems((prevItems) =>
              prevItems.map((item) => {
                if (item.block_id === data.block_id) {
                  return {
                    ...item,
                    data: {
                      ...item.data,
                      content: data.data.content,
                      final: data.data.final,
                    },
                  };
                }
                return item;
              }),
            );
          }
        } else if (existingIndex !== -1) {
          // Message exists in streamItems - update it
          if (data.data.final) {
            // Message is finalized - move to items
            setStreamItems((prevState) => {
              const finalizedMessage = {
                ...prevState[existingIndex],
                data: {
                  ...prevState[existingIndex].data,
                  content: data.data.content,
                  final: data.data.final,
                },
              };

              // Add to items
              setItems((prevItems) => [...prevItems, finalizedMessage]);

              // Remove from streamItems
              return prevState.filter((_, index) => index !== existingIndex);
            });
            setStreaming?.(false);
          } else {
            // Message is still streaming - update content
            setStreamItems((prevState) =>
              prevState.map((item) => {
                if (item.block_id === data.block_id) {
                  setStreaming?.(true);
                  return {
                    ...item,
                    data: {
                      ...item.data,
                      content: data.data.content,
                      final: data.data.final,
                    },
                  };
                }
                return item;
              }),
            );
          }
        } else {
          // New message - add to streamItems
          setStreamItems((prevState) => [...prevState, messageData]);

          if (!data.data.final) {
            setStreaming?.(true);
          }
        }

        // Auto-scroll to bottom
        setScrolledBottom(isScrolledToBottom());
      }
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [lastMessage]);

  /*useEffect(() => {
    if (lastMessage?.data) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      const data = JSON.parse(lastMessage?.data);
      console.log("AppPostReplies lastMessage received", {data});

      // console.log('lastMessage parsed data', data);

      if (data?.event === 'typing') {
        setThinking?.(true);
        // scrollToPostBottom();
      }
      else if (data?.event === 'task_end') {
        setThinking?.(false);
        setStreaming?.(false);
        setDataLoading?.(false);

        setStreamItems((prevState) => {
          setItems((prevItems) => [...prevItems, ...prevState]);

          return [];
        });
        setSystemMessage(null);
        // scrollToPostBottom();
      }
      else if (
        data?.event === 'block' &&
        data?.data?.block_type !== 'sys_msg'
      ) {
        if (data?.data?.block === 'html' || data?.data?.block === 'text') {
          if (data?.data?.data?.content === '' || data?.data?.data?.content) {
            // setThinking(false);
            let context = '';

            if (data?.data?.first || !('streaming' in data.data)) {
              if (data.data.user.role === 'system') {
                setSystemMessage((prevState) => {
                  if (prevState) {
                    return {
                      ...prevState,
                      ...data.data,
                      user: {
                        ...data.data.user,
                        profile_color: prevState.user.profile_color,
                      },
                      items: [...prevState.items, data.data],
                    };
                  } else {
                    return {
                      ...data.data,
                      user: {
                        ...data.data.user,
                        profile_color: getRandomColor(),
                      },
                      items: [data.data],
                    };
                  }
                });
              } else {
                if (data.data.user.user_token) {
                  context = data.data.data.content;
                }

                setStreamItems((prevState) => [
                  ...prevState,
                  {
                    ...data.data,
                    user: {
                      ...data.data.user,
                      profile_color:
                        data.data.user.profile_color || getRandomColor(),
                    },
                    context,
                  },
                ]);
              }
            } else {
              setStreamItems((prevState) =>
                prevState.map((item) => {
                  if (item.block_id === data.data.block_id) {
                    setStreaming?.(true);
                    return {
                      ...item,
                      data: {
                        ...item.data,
                        content: item.data?.content + data.data.data.content,
                      },
                    };
                  } else {
                    return item;
                  }
                })
              );
            }

            if (data?.data?.data?.metadata) {
              setStreamItems((prevState) =>
                prevState.map((item) => {
                  if (item.block_id === data.data.block_id) {
                    // setStreaming(true);

                    return {
                      ...item,
                      data: {
                        ...item.data,
                        metadata: data.data.data.metadata,
                      },
                    };
                  } else {
                    return item;
                  }
                })
              );

              setItems((prevState) =>
                prevState.map((item) => {
                  if (item.block_id === data.data.block_id) {
                    return {
                      ...item,
                      data: {
                        ...item.data,
                        metadata: data.data.data.metadata,
                      },
                    };
                  } else {
                    return item;
                  }
                })
              );

              // scrollToPostBottom();
            }
          }
        } else if (data?.data?.block === 'media') {
          setStreamItems((prevState) => [...prevState, data.data]);
          // scrollToPostBottom();
        }

        if (data?.data && 'streaming' in data.data) {
          if (!data.data.streaming) {
            setStreaming?.(false);

            timerRef.current = setTimeout(() => {
              setStreamItems((prevState) => {
                setSystemMessage(null);
                setItems((prevItems) => [...prevItems, ...prevState]);
                clearTimeout(timerRef.current);
                timerRef.current = null;

                return [];
              });
            }, 10000);
          }
        }
      }

      setScrolledBottom(isScrolledToBottom());
    }

    return () => {
      clearTimeout(timerRef.current);
    };
  }, [lastMessage]);*/

  const onClapClick = useCallback(
    (
      reply: any,
      reactionCount: number,
      isSubReply = false,
      parentReply: any | null = null,
    ) => {
      if (isSubReply && !parentReply) return;
      putDataApi(
        `threads/${reply.block_id}/reaction/?post_type=block`,
        infoViewActionsContext,
        {
          reaction_type: 'clap',
          reaction_count: reactionCount,
        },
        true,
      )
        .then((res: any) => {
          if (res.data?.reaction) {
            infoViewActionsContext.showMessage(res.message);

            setItems((prevState) => {
              const selectedReply = { ...reply };

              if (isSubReply && parentReply) {
                const selectedParentReply = { ...parentReply };
                selectedReply.reaction_count =
                  +selectedReply.reaction_count + reactionCount;

                selectedParentReply.replies = (parentReply.replies || []).map(
                  (item: any) =>
                    item.block_id === selectedReply.block_id
                      ? selectedReply
                      : item,
                );

                return prevState.map((item) =>
                  item.block_id === replyParent?.block_id
                    ? selectedParentReply
                    : item,
                );
              } else {
                selectedReply.reaction_count =
                  +selectedReply.reaction_count + reactionCount;
                return prevState.map((item) =>
                  item.block_id === selectedReply.block_id
                    ? selectedReply
                    : item,
                );
              }
            });

            setStreamItems((prevState) => {
              const selectedReply = { ...reply };

              if (isSubReply && parentReply) {
                const selectedParentReply = { ...parentReply };

                selectedReply.reaction_count =
                  +selectedReply.reaction_count + reactionCount;

                selectedParentReply.replies = (parentReply.replies || []).map(
                  (item: any) =>
                    item.block_id === selectedReply.block_id
                      ? selectedReply
                      : item,
                );

                return prevState.map((item) =>
                  item.block_id === replyParent?.block_id
                    ? selectedParentReply
                    : item,
                );
              } else {
                selectedReply.reaction_count =
                  +selectedReply.reaction_count + reactionCount;
                return prevState.map((item) =>
                  item.block_id === selectedReply.block_id
                    ? selectedReply
                    : item,
                );
              }
            });
          }
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    },
    [],
  );

  const loadOlderMessages = () => {
    setLoadingMore(true);
    getDataApi(
      `conversation/${activePost.post_id}/messages/`,
      infoViewActionsContext,
      {
        page: page + 1,
        page_size: tablePageSize,
      },
    )
      .then((data: any) => {
        setLoadingMore(false);
        if (data.data?.length > 0) {
          if (apiData.data.length === tablePageSize) {
            setHasMoreRecords(true);
            setPage(page + 1);
          } else {
            setHasMoreRecords(false);
          }
          let context = activePost.title;
          setItems((prevState) => [
            ...data.data
              .filter((item: any) => item.block_type !== 'sys_msg')
              .map((item: any) => {
                if (item.user.user_token) {
                  context = item.data.content;
                }

                return {
                  ...item,
                  user: {
                    ...item.user,
                    profile_color: item.user.profile_color || getRandomColor(),
                  },
                  context,
                };
              }),
            ...prevState,
          ]);
        } else {
          setHasMoreRecords(false);
          infoViewActionsContext.showMessage(
            formatMessage({ id: 'common.noMoreData' }),
          );
        }
      })
      .catch((error: any) => {
        setLoadingMore(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  const onMenuClick = useCallback((key: any, block: any) => {
    setSelectedBlock(block);

    if (key === 'delete') {
      setDeleteOpen(true);
    }
  }, []);

  const onBlockDelete = () => {
    if (selectedBlock?.block_id) {
      deleteDataApi(
        `threads/${selectedBlock.block_id}/action/`,
        infoViewActionsContext,
        { post_type: 'block' },
        true,
      )
        .then((data: any) => {
          infoViewActionsContext.showMessage(data.message);
          setItems((prevState) =>
            prevState.filter(
              (item: any) => item.block_id !== selectedBlock.block_id,
            ),
          );

          setStreamItems((prevState) =>
            prevState.filter(
              (item: any) => item.block_id !== selectedBlock.block_id,
            ),
          );

          setDeleteOpen(false);
          setSelectedBlock(null);
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    }
  };

  return (
    <StyledRootContainer>
      <StyledInnerContainer id="post-replies">
        {hasMoreRecords && (
          <StyledMoreContainer>
            <Button
              type="primary"
              shape="round"
              size="small"
              onClick={loadOlderMessages}
              loading={loadingMore}
              ghost
              icon={<MdRefresh fontSize={16} />}
            >
              Load Older Messages
            </Button>
          </StyledMoreContainer>
        )}

        {loading ? (
          <Row align="middle" justify="center" style={{ height: 200 }}>
            <Spin />
          </Row>
        ) : (
          <Fragment>
            {(items || []).length > 0 && (
              <StyledAppList
                data={items || []}
                renderItem={(replyItem: any) => (
                  <ReplyItem
                    key={replyItem.block_id}
                    reply={replyItem}
                    replyParent={replyParent}
                    onReplyClick={onReplyClick}
                    onClapClick={onClapClick}
                    actionsStyle={actionsStyle}
                    onMenuClick={onMenuClick}
                    noteTitle={noteTitle}
                    onSaveNote={onSaveNote}
                  />
                )}
              />
            )}

            {streamItems?.length > 0 && (
              <StyledAppList
                data={streamItems}
                renderItem={(replyItem: any) => (
                  <ReplyItem
                    key={replyItem.block_id}
                    reply={replyItem}
                    replyParent={replyParent}
                    onReplyClick={onReplyClick}
                    onClapClick={onClapClick}
                    actionsStyle={actionsStyle}
                    onMenuClick={onMenuClick}
                    onSaveNote={onSaveNote}
                  />
                )}
              />
            )}

            {systemMessage && (
              <StyledAppList
                data={[systemMessage]}
                renderItem={(replyItem: any) => (
                  <ReplyItem
                    key={replyItem.block_id}
                    reply={replyItem}
                    replyParent={replyParent}
                    onReplyClick={onReplyClick}
                    onClapClick={onClapClick}
                    actionsStyle={actionsStyle}
                    onMenuClick={onMenuClick}
                    onSaveNote={onSaveNote}
                  />
                )}
              />
            )}
          </Fragment>
        )}

        {thinking && !systemMessage && (
          <StyledMsgChat>
            <Text>Analysing</Text>
            <AppDotFlashing />
          </StyledMsgChat>
        )}
      </StyledInnerContainer>

      <StyledScrollBottom
        className={clsx({ 'scrolled-to-bottom': isReachBottom })}
      >
        <Button
          size="large"
          shape="circle"
          icon={<RiArrowDownLine fontSize={24} />}
          onClick={scrollToPostBottom}
        />
      </StyledScrollBottom>

      <AppConfirmModal
        open={isDeleteOpen}
        onOk={onBlockDelete}
        message={formatMessage({ id: 'common.deleteMessage' })}
        onCancel={() => setDeleteOpen(false)}
      />
    </StyledRootContainer>
  );
};

AppPostReplies.displayName = 'PostReplies';

export default memo(AppPostReplies);
