import {Typography} from 'antd';
import {GrResources} from 'react-icons/gr';
import {StyledContent, StyledItemRoot, StyledRoot, StyledTitleWrapper,} from './index.styled';
import {useAppSpaceContext} from '@unpod/providers';
import {useIntl} from 'react-intl';

const {Paragraph, Title} = Typography;

const getLabel = (currentSpace: any) => {
  if (currentSpace?.content_type === 'contact') {
    return 'add.newContact';
  } else if (currentSpace?.content_type === 'conversation') {
    return 'add.newConversation';
  } else if (currentSpace?.content_type === 'note') {
    return 'add.newNote';
  }
  return 'add.newDocument';
};

const AddWidget = ({onClick}: { onClick: () => void }) => {
  const {formatMessage} = useIntl();
  const {currentSpace} = useAppSpaceContext();

  return (
    <StyledRoot>
      <div>
        <StyledItemRoot onClick={onClick}>
          <StyledContent>
            <StyledTitleWrapper>
              <GrResources fontSize={24}/>
              <Title level={4}>
                {formatMessage({id: getLabel(currentSpace)})}
              </Title>
            </StyledTitleWrapper>

            <Paragraph className="mb-0">
              {formatMessage({id: 'add.description'})}
            </Paragraph>
          </StyledContent>
        </StyledItemRoot>
      </div>
    </StyledRoot>
  );
};

export default AddWidget;
