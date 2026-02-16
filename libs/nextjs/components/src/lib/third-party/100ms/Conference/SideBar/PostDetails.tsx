import React, { useCallback, useEffect, useRef, useState } from 'react';
import useWebSocket from 'react-use-websocket';
import {
  putDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppPostReplies from '../../../../modules/AppPostReplies';
import { StyledScrollbar } from './index.styled';
import AppPostQuestionWindow from '../../../../modules/AppPostQuestionWindow';
import AppPostView from '../../../../modules/AppPostView';
import {
  useOrgActionContext,
  useOrgContext,
} from '@unpod/providers';
import { useStreamContext } from '../../StreamContextProvider';

const PostDetails: React.FC = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { currentPost } = useOrgContext();
  const { setCurrentPost } = useOrgActionContext();
  const didUnmount = useRef(false);
  const { visitorId, isAuthenticated } = useAuthContext();
  const { post, token } = useStreamContext() || {};

  let parmas: Record<string, any> = {
    token,
    app_type: process.env.appType,
  };
  if (!isAuthenticated) {
    parmas = { session_user: visitorId, app_type: process.env.appType };
  }

  const [replyParent, setReplyParent] = useState(null);
  const [thinking, setThinking] = useState(false);
  const rootRef = React.useRef<any>(null);

  const { sendJsonMessage, lastMessage } = useWebSocket(
    `${process.env.chatApiUrl}conversation/${post?.post_id}/`,
    {
      queryParams: parmas,
      shouldReconnect: (closeEvent) => {
        /*
        useWebSocket will handle unmounting for you, but this is an example of a
        case in which you would not want it to automatically reconnect
      */
        return didUnmount.current === false;
      },
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    }
  );

  useEffect(() => {
    if (currentPost && post && currentPost.post_id !== post.post_id) {
      setCurrentPost(post);
    }
  }, [post]);

  useEffect(() => {
    return () => {
      didUnmount.current = true;
    };
  }, []);

  const scrollToBottom = () => {
    setTimeout(() => {
      const offsetTop = document.getElementById('post-reply-end')?.offsetTop || 0;
      if (offsetTop > window.outerHeight / 2) {
        const scrollEl = rootRef.current?.getScrollElement();
        scrollEl?.scrollTo({
          top: offsetTop,
          behavior: 'smooth',
        });
      }
    }, 100);
  };

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);

      if (data?.data) {
        scrollToBottom();
      }
    }
  }, [lastMessage]);

  const onClapClick = useCallback(
    (reactionCount: number) => {
      putDataApi(
        `threads/${currentPost.slug}/reaction/`,
        infoViewActionsContext,
        {
          reaction_type: 'clap',
          reaction_count: reactionCount,
        },
        true
      )
        .then((res) => {
          if (res.data?.reaction) {
            const count = +currentPost.reaction_count + reactionCount;
            setCurrentPost({ ...currentPost, reaction_count: count });
            infoViewActionsContext.showMessage(res.message);
          }
        })
        .catch((error) => {
          infoViewActionsContext.showError(error.message);
        });
    },
    [post]
  );

  const onReplyPost = () => {
    setReplyParent(null);
  };

  return (
    <StyledScrollbar ref={rootRef}>
      <AppPostView
        post={post}
        onClapClick={onClapClick}
        onReplyPost={onReplyPost}
        isStreamView
      />

      {currentPost && (
        <AppPostReplies
          lastMessage={lastMessage}
          activePost={currentPost}
          replyParent={replyParent}
          setReplyParent={setReplyParent}
          thinking={thinking}
          actionsStyle={{
            position: 'relative',
            top: 0,
            right: 0,
            padding: 0,
          }}
        />
      )}

      <div id="post-reply-end" style={{ marginBottom: 20 }} />

      <AppPostQuestionWindow
        currentPost={currentPost}
        replyParent={replyParent}
        setReplyParent={setReplyParent}
        sendJsonMessage={sendJsonMessage}
        lastMessage={lastMessage}
        setThinking={setThinking}
        rootStyle={{
          maxWidth: 'calc(100% - 1px)',
          bottom: 16,
          marginBottom: 16,
        }}
        overlayStyle={{
          position: 'absolute',
          top: 0,
          bottom: 0,
          left: 0,
          right: 0,
          width: '100%',
          height: '100%',
        }}
        placeholder="Type here..."
      />
    </StyledScrollbar>
  );
};

export default PostDetails;
