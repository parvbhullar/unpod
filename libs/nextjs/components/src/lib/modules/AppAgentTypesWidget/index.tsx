import type {FC} from 'react';
import {Typography} from 'antd';
import AppImage from '../../next/AppImage';
import {StyledContainer, StyledContent, StyledItemRoot, StyledRoot, StyledTitleWrapper,} from './index.styled';
import {useIntl} from 'react-intl';

const items = [
  {
    key: 'doc',
    titleId: 'agentTypes.knowledgeTitle',
    image: '/images/icons/discover.svg',
    descriptionId: 'agentTypes.knowledgeDescription',
  },
  {
    key: 'chat',
    titleId: 'agentTypes.conversationsTitle',
    image: '/images/icons/conversation.svg',
    descriptionId: 'agentTypes.conversationsDescription',
  },
  {
    key: 'note',
    titleId: 'agentTypes.notesTitle',
    image: '/images/icons/speech-voice.svg',
    descriptionId: 'agentTypes.notesDescription',
  },
];

const {Paragraph, Title} = Typography;

const AppAgentTypesWidget: FC = () => {
  const {formatMessage} = useIntl();
  const handleItemClick = (key: string) => {
    // setActiveTab?.(key);
  };

  return (
    <StyledRoot>
      {/*<Title level={2}>A Smarter Way to Connect, Capture, and Create</Title>*/}

      <StyledContainer>
        {items.map((item) => (
          <StyledItemRoot
            key={item.key}
            onClick={() => handleItemClick(item.key)}
          >
            <StyledContent>
              <StyledTitleWrapper>
                <Title level={4}>{formatMessage({id: item.titleId})}</Title>
                <AppImage
                  src={item.image}
                  alt={item.titleId}
                  height={36}
                  width={36}
                />
              </StyledTitleWrapper>
              <Paragraph className="mb-0">
                {formatMessage({id: item.descriptionId})}
              </Paragraph>
            </StyledContent>
          </StyledItemRoot>
        ))}
      </StyledContainer>
    </StyledRoot>
  );
};

export default AppAgentTypesWidget;
