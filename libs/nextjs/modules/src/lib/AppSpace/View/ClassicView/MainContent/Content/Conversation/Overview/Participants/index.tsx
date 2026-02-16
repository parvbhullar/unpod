import { Fragment } from 'react';
import {
  StyledDateHeader,
  StyledDateSection,
  StyledDateText,
  StyledText,
} from './index.styled';
import ListItems from '../ListItems';
import { Badge, Space } from 'antd';
import { getOverviewData } from '../data';
import UserAvatar from '@unpod/components/common/UserAvatar';

const Participants = ({ activeConversation }: { activeConversation: any }) => {
  return (
    <StyledDateSection>
      <StyledDateHeader strong type="secondary">
        PARTICIPANTS
      </StyledDateHeader>
      {getOverviewData(activeConversation).participants.map((participant) => (
        <ListItems
          key={participant.id}
          avatar={<UserAvatar user={participant as any} />}
          title={participant.name}
          description={
            <Space size={4} wrap>
              <StyledText type="secondary">{participant.role}</StyledText>
              {participant.time && (
                <Fragment>
                  <Badge dot status="default" />

                  <StyledDateText type="secondary">
                    {participant.time}
                  </StyledDateText>
                </Fragment>
              )}
            </Space>
          }
        />
      ))}
    </StyledDateSection>
  );
};

export default Participants;
