import { currentTime, duration, progress } from '../data';
import {
  StyledAudioInfo,
  StyledAudioPlayer,
  StyledDateHeader,
  StyledDateSection,
  StyledPlayButton,
  StyledSecoundryButton,
  StyledText,
  StyledTextWrapper,
  StyledTimeDisplay,
  StyledTimeText,
} from './index.styled';
import { Progress, Tooltip } from 'antd';
import { MdDownload, MdPlayArrow } from 'react-icons/md';

const ConversationRecording = ({
  activeConversation,
}: {
  activeConversation: any;
}) => {
  return (
    <StyledDateSection>
      <StyledDateHeader strong type="secondary">
        AUDIO RECORDING
      </StyledDateHeader>

      <StyledAudioPlayer>
        <Tooltip title="Play">
          <StyledPlayButton icon={<MdPlayArrow size={18} />} />
        </Tooltip>
        <StyledAudioInfo>
          <StyledTextWrapper>
            <StyledText strong>Conversation Recording</StyledText>
            <StyledTimeText type="secondary">{duration}</StyledTimeText>
          </StyledTextWrapper>
          <Progress
            percent={progress}
            showInfo={false}
            strokeColor="#796CFF"
            trailColor="#F7F7F7"
          />
          <StyledTimeDisplay>
            <StyledTimeText type="secondary">{currentTime}</StyledTimeText>
            <StyledTimeText type="secondary">{duration}</StyledTimeText>
          </StyledTimeDisplay>
        </StyledAudioInfo>
        <StyledSecoundryButton icon={<MdDownload size={14} />}>
          Download
        </StyledSecoundryButton>
      </StyledAudioPlayer>
    </StyledDateSection>
  );
};

export default ConversationRecording;
