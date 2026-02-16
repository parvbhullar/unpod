import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import { StyledDocumentsList, StyledRoot } from './index.styled';
import { getOverviewData } from './data';
import ConversationRecording from './ConversationRecording';
import ConversationSummary from './ConversationSummary';
import KeyPoints from './KeyPoints';
import PreviousConversations from './PreviousConversations';
import Participants from './Participants';

const ConversationOverview = () => {
  const { setActiveConversation } = useAppSpaceActionsContext();
  const { activeConversation, token } = useAppSpaceContext();

  if (!activeConversation) {
    return null;
  }

  return (
    <StyledRoot>
      <StyledDocumentsList>
        {getOverviewData(activeConversation).hasAudio && (
          <ConversationRecording activeConversation={activeConversation} />
        )}
        <ConversationSummary
          token={token}
          currentPost={activeConversation}
          setCurrentPost={setActiveConversation}
        />
        <KeyPoints />
        <Participants activeConversation={activeConversation} />
        <PreviousConversations />
      </StyledDocumentsList>
    </StyledRoot>
  );
};

export default ConversationOverview;
