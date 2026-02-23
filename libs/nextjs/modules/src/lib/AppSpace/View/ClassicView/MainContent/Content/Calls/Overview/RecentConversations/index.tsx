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
import {BsChatRightDots} from 'react-icons/bs';
import AppList from '@unpod/components/common/AppList';
import {getFormattedDate} from '@unpod/helpers/DateHelper';
import {AppStatusBadge} from '@unpod/components/common/AppStatusBadge';

const {Text} = Typography;

const RecentConversations = ({
                               recentConversations = [],
                             }: {
  recentConversations?: any[];
}) => {
  return (
    <StyledRoot>
      <StyledContainer>
        <Flex gap={5} align={'center'}>
          <BsChatRightDots size={15}/>
          <Text strong>Recent Conversations</Text>
        </Flex>
        <AppList
          data={recentConversations}
          itemSpacing={16}
          renderItem={(item: any, index: number) => (
            <StyledCard
              key={index}
              title={
                <StyledTimeRow>
                  <StyledTimeText>{getFormattedDate(item.date)}</StyledTimeText>
                  <Badge dot={true} status="default"/>
                  <StyledTimeText>
                    {getFormattedDate(item.date, 'HH:mm')}
                  </StyledTimeText>
                </StyledTimeRow>
              }
              extra={<StyledTime>{item.duration}</StyledTime>}
            >
              <Text type="secondary">{item.summary}</Text>

              <StyledFooter>
                <Flex gap={4} align="center">
                  {/*<MdOutlineWatchLater size={14} />*/}
                  {item.labels?.map((label: any, idx: number) => (
                    <AppStatusBadge
                      key={idx}
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
          )}
        />
      </StyledContainer>
    </StyledRoot>
  );
};

export default RecentConversations;
