import React from 'react';
import { FiPhone } from 'react-icons/fi';
import Button from '../../components/Button';
import {
  InfoSection,
  Label, StyledButton,
  WidgetContainer,
} from './AppChatWidget.styled';
import { useIntl } from 'react-intl';
import { IoMdPlay } from 'react-icons/io';

interface AppChatWidgetProps {
  startCallText?: string;
  actionText?: string;
  onClick?: () => void;
}

export const AppChatWidget: React.FC<AppChatWidgetProps> = ({
  startCallText = 'Start New Test',
  actionText,
  onClick,
}) => {
  const { formatMessage } = useIntl();
  return (
    <WidgetContainer className="chat-widget">
      {/*<AnimatedSphere size={60} />*/}
      <InfoSection className="widget-info-section">
        {actionText && (
          <Label className="widget-action-text">{actionText}</Label>
        )}
        <StyledButton
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
