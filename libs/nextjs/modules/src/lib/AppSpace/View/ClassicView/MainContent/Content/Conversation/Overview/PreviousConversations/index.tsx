import { Fragment } from 'react';
import {
  StyledDateHeader,
  StyledDateSection,
  StyledText,
  StyledTimeText,
} from './index.styled';
import { Flex } from 'antd';
import { previousConversations } from '../data';
import ListItems from '../ListItems';
import UserAvatar from '@unpod/components/common/UserAvatar';

const PreviousConversations = () => {
  return (
    <StyledDateSection>
      <StyledDateHeader strong type="secondary">
        PREVIOUS CONVERSATIONS WITH PS
      </StyledDateHeader>
      {previousConversations.map((conversation) => (
        <Fragment key={conversation.id}>
          <ListItems
            avatar={<UserAvatar user={conversation.user} />}
            title={
              <Flex justify="space-between">
                <StyledText ellipsis={{ tooltip: true }}>
                  {conversation.title}
                </StyledText>
                <StyledTimeText type="secondary">
                  {conversation.time}
                </StyledTimeText>
              </Flex>
            }
            description={conversation.preview}
          />
        </Fragment>
      ))}
    </StyledDateSection>
  );
};

export default PreviousConversations;
