import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import { Modal } from 'antd';
import { useRouter } from 'next/navigation';
import { LiveKitRoom } from '@livekit/components-react';
import { deleteDataApi, useAuthContext, useInfoViewActionsContext } from '@unpod/providers';
import { useTokenGeneration } from '@unpod/livekit/hooks/useTokenGeneration';
import { isViewDetailAllowed } from '@unpod/helpers/PermissionHelper';
import RequestPost from './RequestPost';
import ReportPost from './ReportPost';
import { StyledContainer, StyledNoAccessContainer } from './index.styled';
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';
import AppConfirmModal from '@unpod/components/antd/AppConfirmModal';
import AppConversation from '../AppConversation';
import { useIntl } from 'react-intl';
import useCentrifugoDataChannel from '@unpod/livekit/hooks/useCentrifugoDataChannel';
import { Conversation } from '@unpod/constants';
import { CENTRIFUGO_URL } from '@unpod/constants/ConfigConsts';

/**
 * AppPostContent - Inner content component for post detail view
 *
 * IMPORTANT: This component assumes access control has already been verified
 * by the parent AppPost component. Do not render directly without permission checks.
 *
 * @param {string} token - Authentication token
 * @param {Object} currentPost - Post data object with conversation details
 * @param {Function} onEditPost - Callback for post editing
 * @param {Function} onDeletedPost - Callback for post deletion
 * @param {Function} onStartVoice - Callback to initialize voice connection
 * @returns {ReactNode} JSX Element for post content and conversation interface
 */
type AppPostContentProps = {
  token?: string;
  currentPost: any;
  onEditPost?: () => void;
  onDeletedPost?: () => void;
  onStartVoice?: (options?: Record<string, unknown>) => Promise<any> | void;
  isGeneratingToken?: boolean;
  centrifugoConfig?: any;
};

const AppPostContent = ({
  token,
  currentPost,
  onEditPost,
  onDeletedPost,
  onStartVoice,
  isGeneratingToken,
  centrifugoConfig,
}: AppPostContentProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { isAuthenticated, visitorId } = useAuthContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const [isReportOpen, setReportOpen] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [, setStreaming] = useState(false);
  const [, setDataLoading] = useState(true);
  let params: Record<string, any> = {
    token,
  };

  if (!isAuthenticated) {
    params = { session_user: visitorId };
  }

  // Use hybrid messaging: LiveKit data channel (voice mode) or WebSocket (text-only mode)
  const {
    sendJsonMessage,
    lastMessage,
    voiceAssistant,
    testReceive,
    onLocationResponse,
  } = useCentrifugoDataChannel({
    conversationId: currentPost?.post_id,
    params,
    enabled: true, // Always enabled - uses WebSocket for text-only, LiveKit for voice
    centrifugoConfig: {
      url: CENTRIFUGO_URL!,
      token: centrifugoConfig?.token,
      channel_name: centrifugoConfig?.channel_name,
      agent_name: centrifugoConfig?.agent_name,
      space_token: centrifugoConfig?.space_token,
      metadata: centrifugoConfig?.metadata,
    },
  });

  // console.log('AppPostContent lastMessage', lastMessage);

  // Expose testReceive to window for debugging
  useEffect(() => {
    if (testReceive) {
      (window as any).__testReceive = testReceive;
      console.log(
        '🔍 Debug: Run window.__testReceive() in console to test message reception',
      );
    }
    return () => {
      delete (window as any).__testReceive;
    };
  }, [testReceive]);

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
        if (onDeletedPost) {
          onDeletedPost();
        } else {
          router.push(`/${currentPost?.organization?.domain_handle}/org`);
        }
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onReportPost = () => {
    router.push(`/${currentPost?.organization?.domain_handle}/org`);
  };

  return (
    <Fragment>
      <StyledContainer>
        <AppConversation
          currentPost={currentPost}
          lastMessage={lastMessage}
          thinking={thinking}
          setThinking={setThinking}
          setStreaming={setStreaming}
          setDataLoading={setDataLoading}
          sendJsonMessage={sendJsonMessage as any}
          onStartVoice={onStartVoice as any}
          voiceAssistant={voiceAssistant}
          onLocationResponse={onLocationResponse as any}
          isGeneratingToken={isGeneratingToken}
        />
      </StyledContainer>

      <Modal
        title={formatMessage({ id: 'report.title' })}
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
        message={formatMessage({ id: 'post.deleteConfirm' })}
        onCancel={() => setDeleteOpen(false)}
      />
    </Fragment>
  );
};

// Wrapper component with LiveKitRoom
type AppPostProps = {
  token?: string;
  currentPost: Conversation;
  onEditPost?: () => void;
  onDeletedPost?: () => void;
  shouldAutoStartVoice?: boolean;
  onVoiceStarted?: () => void;
};

const AppPost = ({
  token,
  currentPost,
  onEditPost,
  onDeletedPost,
  shouldAutoStartVoice,
  onVoiceStarted,
}: AppPostProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {
    shouldConnect,
    wsUrl,
    roomToken,
    updateRoomToken,
    connect,
    setConnectionMode,
    connectionMode,
  } = useAgentConnection() as any;

  // Use unified token generation hook
  const {
    generateToken: generateVoiceToken,
    isGenerating: isGeneratingToken,
    responseData: centrifugoConfig,
  } = useTokenGeneration({
    endpoint: `core/voice/${currentPost.parent_post_slug}/generate_room_token/`,
    method: 'GET',
    cacheToken: true,
    onSuccess: (token: any) => {
      console.log('✅ Voice token received and cached');
      updateRoomToken(token);
    },
  });

  const onStartVoice = useCallback(
    async (options = {}) => {
      try {
        // Determine mode based on content_type: 'text' = chat mode, 'voice' = voice mode
        const isVoiceMode = currentPost.content_type === 'voice';
        setConnectionMode(currentPost.content_type);
        const params = {
          source: 'superkik',
          ...(!isVoiceMode && { multimodality: 'text' }), // Add multimodality:'text' for text/chat mode only
          ...options,
        };

        console.log(
          `🎤 Generating token for ${isVoiceMode ? 'VOICE' : 'TEXT'} mode with params:`,
          params,
        );
        return await generateVoiceToken(params);
      } catch (error) {
        console.error('Failed to start voice:', error);
        throw error;
      }
    },
    [generateVoiceToken, currentPost.content_type],
  );

  // Track if we've already auto-started voice for the current shouldAutoStartVoice flag
  const hasAutoStartedRef = useRef(false);

  // Auto-generate voice token ONLY when shouldAutoStartVoice is true (new thread created)
  useEffect(() => {
    if (
      shouldAutoStartVoice &&
      !roomToken &&
      !isGeneratingToken &&
      !hasAutoStartedRef.current
    ) {
      hasAutoStartedRef.current = true;
      console.log(
        `🎤 Auto-starting voice for NEW thread (content_type: ${currentPost.content_type})`,
      );

      onStartVoice()
        .then(() => {
          console.log(
            '✅ Voice token auto-generated successfully for new thread',
          );
          if (onVoiceStarted) {
            onVoiceStarted();
          }
        })
        .catch((error) => {
          console.error('❌ Failed to auto-generate voice token:', error);
          // Reset flag on error so user can retry manually
          hasAutoStartedRef.current = false;
        });
    }
  }, [
    shouldAutoStartVoice,
    roomToken,
    isGeneratingToken,
    currentPost.content_type,
  ]);

  // Reset the auto-start flag when shouldAutoStartVoice changes from false to true
  useEffect(() => {
    if (shouldAutoStartVoice) {
      hasAutoStartedRef.current = false;
    }
  }, [shouldAutoStartVoice]);

  // Auto-connect to LiveKit room when token is available
  // Only auto-connect in 'env' mode - don't override manual voice connections
  useEffect(() => {
    if (roomToken && !shouldConnect && connectionMode === 'env') {
      console.log('📡 Auto-connecting to LiveKit in env mode');
      connect();
    }
  }, [roomToken, shouldConnect, connectionMode, connect]);

  console.log('AppPost roomToken', roomToken);

  return (
    <Fragment>
      {isViewDetailAllowed(undefined, currentPost, undefined) ||
      currentPost.privacy_type === 'public' ? (
        <LiveKitRoom
          serverUrl={wsUrl}
          token={roomToken || undefined}
          connect={shouldConnect}
          onError={(e: any) => {
            infoViewActionsContext.showError(e.message);
            console.error('LiveKitRoom Error', e);
          }}
        >
          <AppPostContent
            token={token}
            currentPost={currentPost}
            onEditPost={onEditPost}
            onDeletedPost={onDeletedPost}
            onStartVoice={onStartVoice as any}
            isGeneratingToken={isGeneratingToken}
            centrifugoConfig={centrifugoConfig}
          />
        </LiveKitRoom>
      ) : (
        <StyledNoAccessContainer>
          <RequestPost post={currentPost} />
        </StyledNoAccessContainer>
      )}
    </Fragment>
  );
};

export default AppPost;
