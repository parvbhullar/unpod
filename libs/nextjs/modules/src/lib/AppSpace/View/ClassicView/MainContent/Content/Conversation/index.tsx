import { Fragment, useEffect, useState } from 'react';
import { useBottomScrollListener } from 'react-bottom-scroll-listener';

import {
  getDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { AgentConnectionProvider } from '@unpod/livekit/hooks/useAgentConnection';
import {
  StyledAskContainer,
  StyledContainer,
  StyledRoot,
} from '../../index.styled';
import AppPost from '../../../../../../AppPost';

import ConversationOverview from './Overview';
import { useRouter } from 'next/navigation';
import Tasks from './Tasks';
import AppQueryWindow from '@unpod/components/modules/AppQueryWindow';
import AnimatedSphere from '@unpod/livekit/AppVoiceAgent/AnimatedSphere'; // import { UnpodLogoAnimation } from '@unpod/components';
// import { UnpodLogoAnimation } from '@unpod/components';

const Conversation = () => {
  const {
    setActiveConversation,
  } = useAppSpaceActionsContext();
  const {
    activeConversation,
    currentSpace,
    token,
    activeTab,
    conversationsRef,
  } = useAppSpaceContext();
  const router = useRouter();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [, setScrolled] = useState(false);
  const [activeTabs] = useState('conversation');
  const [shouldAutoStartVoice, setShouldAutoStartVoice] = useState(false);

  const containerRef = useBottomScrollListener(
    () => {
      console.log('Bottom reached');
    },
    {
      offset: 200,
      debounce: 200,
      triggerOnNoScroll: false,
    },
  ) as any;

  useEffect(() => {
    const handler = () => {
      // no-op for now
      setScrolled(false);
    };
    if (containerRef?.current) {
      containerRef.current.addEventListener('scroll', handler);
    }

    return () => {
      if (containerRef?.current) {
        containerRef.current.removeEventListener('scroll', handler);
      }
    };
  }, []);

  const onDataSaved = (data: any) => {
    // Fetch full thread details to get messages
    getDataApi(`threads/${data.slug}/detail/`, infoViewActionsContext)
      .then((response: any) => {
        const threadWithMessages = response.data;

        // Mark this as a newly created thread to auto-start voice
        threadWithMessages._isNewThread = true;

        setActiveConversation(threadWithMessages);
        router.replace(
          `/spaces/${currentSpace!.slug}/${activeTab}/${data.slug}`,
        );

        // Add new conversation to the top of the sidebar list
        if (conversationsRef?.current?.addConversation) {
          conversationsRef.current.addConversation(data);
        }

        // Set flag to auto-start voice after conversation is set
        setShouldAutoStartVoice(true);
      })
      .catch((error: any) => {
        console.error('Failed to fetch thread details:', error);
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <StyledRoot ref={containerRef}>
      {activeConversation ? (
        <Fragment>
          {activeTabs.includes('overview') && <ConversationOverview />}
          {activeTabs.includes('tasks') && <Tasks />}
          {activeTabs.includes('conversation') && (
            <AgentConnectionProvider>
              <AppPost
                token={token}
                currentPost={activeConversation}
                onDeletedPost={() => setActiveConversation(null)}
                shouldAutoStartVoice={shouldAutoStartVoice}
                onVoiceStarted={() => setShouldAutoStartVoice(false)}
              />
            </AgentConnectionProvider>
          )}
        </Fragment>
      ) : (
        <StyledContainer>
          {/*<UnpodLogoAnimation showOrbits={false}/>*/}
          <AnimatedSphere
            size={250}
            breakpoints={{
              mobile: 200, // < 768px
              tablet: 230, // 768-1023px
              desktop: 250, // ≥ 1024px
            }}
          />

          <StyledAskContainer>
            {/*
              <StyledInfoContainer>
                <Typography.Title level={2}>
                  How can we assist you today?
                </Typography.Title>

                <Typography.Paragraph type="secondary">
                  Upload knowledge, chat with AI agents, or save important notes
                  — all in one place.
                </Typography.Paragraph>
              </StyledInfoContainer>*/}

            <AppQueryWindow
              pilotPopover
              onDataSaved={onDataSaved}
              executionType={currentSpace?.content_type}
              defaultKbs={currentSpace?.slug ? [currentSpace?.slug] : []}
              isMySpace
            />

            {/*<AppAgentTypesWidget setActiveTab={setActiveTab} />*/}
          </StyledAskContainer>
          {/*<StyledAskContainer $isScrolled={isScrolled}>
            <AppAgentTypesWidget setActiveTab={setActiveTab} />
          </StyledAskContainer>*/}
        </StyledContainer>
      )}
    </StyledRoot>
  );
};

Conversation.displayName = 'Conversation';

export default Conversation;
