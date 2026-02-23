import {Fragment, useCallback, useEffect, useRef, useState} from 'react';
import {Modal} from 'antd';
import {deleteDataApi, putDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import AppPostView from '@unpod/components/modules/AppPostView';
import {useParams, useRouter} from 'next/navigation';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import AppPostReplies from '@unpod/components/modules/AppPostReplies';
import useWebSocket from 'react-use-websocket';
import PageHeader from './PageHeader';
import PilotInputWindow from './PilotInputWindow';
import ReportPost from './ReportPost';
import {StyledContainer, StyledDetailsRoot, StyledThreadContainer,} from './index.styled';
import AppConfirmModal from '@unpod/components/antd/AppConfirmModal';
import {useIntl} from 'react-intl';

type AppThreadModuleProps = {
  token?: string;
  post: any;
};

const AppThreadModule = ({token, post}: AppThreadModuleProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {isAuthenticated, visitorId} = useAuthContext();
  const router = useRouter();
  const {orgSlug, spaceSlug, postSlug} = useParams() as {
    orgSlug?: string;
    spaceSlug?: string;
    postSlug?: string;
  };
  const {formatMessage} = useIntl();

  const didUnmount = useRef(false);

  const [currentPost, setCurrentPost] = useState(post);

  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const [isReportOpen, setReportOpen] = useState(false);
  const [replyParent, setReplyParent] = useState(null);

  let params: Record<string, any> = {
    token,
    app_type: process.env.appType || '',
  };

  if (!isAuthenticated) {
    params = {session_user: visitorId, app_type: process.env.appType || ''};
  }

  /*useEffect(() => {
    setCurrentPost(post);
  }, [post]);*/

  const {sendJsonMessage, lastMessage} = useWebSocket(
    `${process.env.chatApiUrl}conversation/${currentPost?.post_id}/`,
    {
      queryParams: params,
      shouldReconnect: (closeEvent) => {
        /*
        useWebSocket will handle unmounting for you, but this is an example of a
        case in which you would not want it to automatically reconnect
      */
        return didUnmount.current === false;
      },
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    },
  );

  useEffect(() => {
    return () => {
      didUnmount.current = true;
    };
  }, []);

  const onClapClick = useCallback(
    (reactionCount: number) => {
      putDataApi(
        `threads/${currentPost.slug}/reaction/`,
        infoViewActionsContext,
        {
          reaction_type: 'clap',
          reaction_count: reactionCount,
        },
        true,
      )
        .then((res: any) => {
          if (res.data?.reaction) {
            const count = +currentPost.reaction_count + reactionCount;
            setCurrentPost({...currentPost, reaction_count: count});
            infoViewActionsContext.showMessage(res.message);
          }
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    },
    [currentPost],
  );

  const onDeletePost = () => {
    setDeleteOpen(false);

    deleteDataApi(
      `threads/${currentPost.slug}/action/`,
      infoViewActionsContext,
      {},
      true,
    )
      .then((data: any) => {
        infoViewActionsContext.showMessage(data.message);
        router.push(`/${currentPost?.organization?.domain_handle}/org`);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onMenuClick = (key: string) => {
    if (key === 'delete') {
      setDeleteOpen(true);
    } else if (key === 'edit') {
      router.push(`/${orgSlug}/${spaceSlug}/${postSlug}/edit/`);
    } else if (key === 'report') {
      setReportOpen(true);
    }
  };

  const onReportPost = () => {
    router.push(`/${currentPost?.organization?.domain_handle}/org`);
  };

  const onReplyPost = () => {
    setReplyParent(null);
  };

  return (
    <Fragment>
      <PageHeader currentPost={currentPost} setCurrentPost={setCurrentPost}/>

      <AppPageContainer>
        <StyledThreadContainer>
          <StyledContainer>
            <StyledDetailsRoot>
              <AppPostView
                post={currentPost}
                setCurrentPost={setCurrentPost}
                onClapClick={onClapClick}
                onMenuClick={onMenuClick}
                onReplyPost={onReplyPost}
                lastMessage={lastMessage}
              />

              {/*<Sources />

              <RelatedQueries />*/}

              {/*{isAuthenticated && (
                <AppPostReplies
                  lastMessage={lastMessage}
                  activePost={currentPost}
                  replyParent={replyParent}
                  setReplyParent={setReplyParent}
                />
              )}*/}

              <AppPostReplies
                lastMessage={lastMessage}
                activePost={currentPost}
                replyParent={replyParent}
                setReplyParent={setReplyParent}
              />

              <div id="post-reply-end"/>
            </StyledDetailsRoot>

            <PilotInputWindow
              currentPost={currentPost}
              replyParent={replyParent}
              setReplyParent={setReplyParent}
              sendJsonMessage={sendJsonMessage}
            />
          </StyledContainer>
        </StyledThreadContainer>
      </AppPageContainer>

      <Modal
        title={formatMessage({id: 'report.title'})}
        footer={false}
        open={isReportOpen}
        destroyOnHidden={true}
        onCancel={() => setReportOpen(false)}
      >
        <ReportPost
          onClose={() => setReportOpen(false)}
          post={currentPost}
          onReportPost={onReportPost}
        />
      </Modal>

      <AppConfirmModal
        open={isDeleteOpen}
        onOk={onDeletePost}
        message={formatMessage({id: 'post.deleteConfirm'})}
        onCancel={() => setDeleteOpen(false)}
      />
    </Fragment>
  );
};

export default AppThreadModule;
