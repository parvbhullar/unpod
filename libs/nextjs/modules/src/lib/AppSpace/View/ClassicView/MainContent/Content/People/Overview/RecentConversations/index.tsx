import {
  StyledCard,
  StyledContainer,
  StyledFooter,
  StyledRoot,
  StyledTime,
  StyledTimeRow,
  StyledTimeText,
} from './index.styled';
import {Badge, Flex, Typography} from 'antd';
import {StyledDateHeader} from '../Summary/index.styled';
import {BsChatRightDots} from 'react-icons/bs';
import AppList from '@unpod/components/common/AppList';
import {getFormattedDate} from '@unpod/helpers/DateHelper';
import {AppStatusBadge} from '@unpod/components/common/AppStatusBadge';

const {Text} = Typography;

type RecentConversation = {
  date?: string;
  duration?: string;
  summary?: string;
  labels?: string[];
  exchanges?: string;
};

type RecentConversationsProps = {
  recentConversations?: RecentConversation[];
};

const RecentConversations = ({
                               recentConversations = [],
                             }: RecentConversationsProps) => {
  return (
    <StyledRoot>
      <StyledContainer>
        <Flex gap={5} align={'center'}>
          <BsChatRightDots size={15}/>
          <StyledDateHeader strong>Recent Conversations</StyledDateHeader>
        </Flex>
        <AppList
          data={recentConversations}
          itemSpacing={16}
          renderItem={(item, index) => {
            const conversation = item as RecentConversation;
            const dateValue = conversation.date || '';
            return (
              <StyledCard
                key={index}
                title={
                  <StyledTimeRow>
                    <StyledTimeText>
                      {getFormattedDate(dateValue)}
                    </StyledTimeText>
                    <Badge dot={true} status="default"/>
                    <StyledTimeText>
                      {getFormattedDate(dateValue, 'HH:mm')}
                    </StyledTimeText>
                  </StyledTimeRow>
                }
                extra={<StyledTime>{conversation.duration}</StyledTime>}
              >
                <Text type="secondary">{conversation.summary}</Text>

                <StyledFooter>
                  <Flex gap={4} align="center">
                    {/*<MdOutlineWatchLater size={14} />*/}
                    {conversation.labels?.map((label) => (
                      <AppStatusBadge
                        key={label}
                        status={label}
                        name={label}
                        size="small"
                      />
                    ))}
                  </Flex>
                  {/*<Flex gap={4} align="center">*/}
                  {/*  <BsChatRightDots size={10} />*/}
                  {/*  <StyledText type="secondary">{item.exchanges}</StyledText>*/}
                  {/*</Flex>*/}
                </StyledFooter>
              </StyledCard>
            );
          }}
        />
      </StyledContainer>
    </StyledRoot>
  );
};

export default RecentConversations;
