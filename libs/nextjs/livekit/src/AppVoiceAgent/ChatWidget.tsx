import React from 'react';
import {FiPhone} from 'react-icons/fi';
import Button from '../components/Button';
import {InfoSection, Label, WidgetContainer} from './ChatWidget.styled';
import {AnimatedSphere} from './AnimatedSphere';
import {useIntl} from 'react-intl';

type ChatWidgetProps = {
  startCallText?: string;
  actionText?: string;
  onClick?: () => void;
};

export const ChatWidget: React.FC<ChatWidgetProps> = ({
                                                        startCallText = 'common.call',
                                                        actionText = 'common.needHelp',
                                                        onClick,
                                                      }) => {
  const {formatMessage} = useIntl();
  return (
    <WidgetContainer className="chat-widget">
      <AnimatedSphere size={60}/>
      <InfoSection className="widget-info-section">
        <Label className="widget-action-text">
          {formatMessage({id: actionText})}
        </Label>
        <Button
          className="widget-button"
          onClick={onClick}
          shape="round"
          variant="primary"
        >
          <FiPhone/>
          {formatMessage({id: startCallText})}
        </Button>
      </InfoSection>
    </WidgetContainer>
  );
};
