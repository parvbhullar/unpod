import {
  selectUnreadHMSMessagesCount,
  useHMSStore,
} from '@100mslive/react-sdk';
import {
  useIsSidepaneTypeOpen,
  useSidepaneToggle,
} from '../../AppData/useSidepane';
import { useIsFeatureEnabled } from '../../hooks/useFeatures';
import { FEATURE_LIST, SIDE_PANE_OPTIONS } from '../../common/constants';
import { Button, Tooltip } from 'antd';
import {
  MdOutlineChatBubbleOutline,
  MdOutlineMarkChatUnread,
} from 'react-icons/md';

export const ChatToggle = () => {
  const countUnreadMessages = useHMSStore(selectUnreadHMSMessagesCount);
  const isChatOpen = useIsSidepaneTypeOpen(SIDE_PANE_OPTIONS.CHAT);
  const toggleChat = useSidepaneToggle(SIDE_PANE_OPTIONS.CHAT);
  const isFeatureEnabled = useIsFeatureEnabled(FEATURE_LIST.CHAT);

  if (!isFeatureEnabled) {
    return;
  }

  return (
    <Tooltip key="chat" title={`${isChatOpen ? 'Close' : 'Open'} chat`}>
      <Button
        onClick={toggleChat}
        active={!isChatOpen}
        data-testid="chat_btn"
        icon={
          countUnreadMessages === 0 ? (
            <MdOutlineChatBubbleOutline />
          ) : (
            <MdOutlineMarkChatUnread data-testid="chat_unread_btn" />
          )
        }
      ></Button>
    </Tooltip>
  );
};
