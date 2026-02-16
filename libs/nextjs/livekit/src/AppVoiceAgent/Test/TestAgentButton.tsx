import { IoMdPlay } from 'react-icons/io';
import { InfoSection, StyledButton, WidgetContainer } from './TestAgent.styled';

type TestAgentButtonProps = {
  startCallText?: string;
  disable?: boolean;
  onClick?: () => void;
};

export const TestAgentButton = ({
  startCallText = 'Start New Test',
  disable,
  onClick,
}: TestAgentButtonProps) => {
  return (
    <WidgetContainer className="chat-widget">
      <InfoSection className="widget-info-section">
        <StyledButton
          disabled={disable}
          className="widget-button"
          onClick={onClick}
          type="primary"
          icon={<IoMdPlay size={18} />}
        >
          {startCallText}
        </StyledButton>
      </InfoSection>
    </WidgetContainer>
  );
};
