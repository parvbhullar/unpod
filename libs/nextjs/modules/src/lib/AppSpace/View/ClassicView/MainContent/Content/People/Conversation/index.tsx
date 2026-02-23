import {useState} from 'react';
import {StyledDescription, StyledTime} from './index.styled';
import UserAvatar from '@unpod/components/common/UserAvatar';
import {Flex, Typography} from 'antd';
import ListItems from '../../Conversation/Overview/ListItems';
import {useAppSpaceActionsContext, useAppSpaceContext, useAuthContext, useGetDataApi,} from '@unpod/providers';
import AppList from '@unpod/components/common/AppList';
import {getTimeFromNow} from '@unpod/helpers/DateHelper';
import ConversationView from './ConversationView';
import {AppDrawer} from '@unpod/components/antd';
import {AppStatusBadge} from '@unpod/components/common/AppStatusBadge';

const {Text} = Typography;
const statusColors = {
  interested: {color: 'badge-success', label: 'Interested'},
  interrested: {color: 'badge-success', label: 'Interested'},
  'not connected': {color: 'badge-error', label: 'Not Connected'},
  'follow up': {color: 'badge-warning', label: 'Follow Up'},
  connected: {color: 'badge-primary', label: 'Connected'},
  scheduled: {color: 'badge-info', label: 'Scheduled'},
  completed: {color: 'badge-success', label: 'Completed'},
  pending: {color: 'badge-warning', label: 'Pending'},
  cancelled: {color: 'badge-error', label: 'Cancelled'},
};

type ConversationItem = {
  content?: string;
  title?: string;
  created?: string;
  description?: string;
  tags?: string[] | string;
  user?: {
    full_name?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

const Conversations = () => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const {activeDocument, activeConversation} = useAppSpaceContext();
  const {setActiveConversation} = useAppSpaceActionsContext();
  const {activeOrg} = useAuthContext();
  const activeConversationData = activeConversation as ConversationItem | null;

  const [{apiData, loading}] = useGetDataApi(
    `threads/connector-doc-data/${activeDocument?.document_id}/`,
    {data: []},
    {
      domain: activeOrg?.domain_handle,
      page_size: 20,
      page: 1,
    },
  ) as unknown as [
    { apiData?: { data?: ConversationItem[] }; loading: boolean },
  ];

  const handleConversationClick = (item: ConversationItem) => {
    setActiveConversation(item);
    setIsDrawerOpen(true);
  };

  const handleDrawerClose = () => {
    setIsDrawerOpen(false);
  };

  return (
    <>
      <AppList
        style={{
          height: 'calc(100vh - 230px)',
          padding: '20px 0 0 0',
        }}
        data={apiData?.data ?? []}
        itemSpacing={16}
        loading={loading}
        renderItem={(item) => {
          const conversation = item as ConversationItem;
          return (
            <ListItems
              onClick={() => handleConversationClick(conversation)}
              avatar={<UserAvatar user={conversation.user} size={48}/>}
              title={
                <Flex vertical gap={2}>
                  <Flex justify="space-between" align="center">
                    <Text
                      strong
                      style={{fontSize: 15, color: '#262626', flex: 1}}
                      ellipsis
                    >
                      {conversation.content ||
                        conversation.title ||
                        'No content'}
                    </Text>
                    <StyledTime
                      style={{margin: '0 0 0 12px', fontSize: 12}}
                      type="secondary"
                    >
                      {getTimeFromNow(conversation.created)}
                    </StyledTime>
                  </Flex>
                  <Flex align="center" gap={8} wrap="wrap">
                    <Text
                      style={{
                        fontSize: 13,
                        color: '#8c8c8c',
                        fontWeight: 400,
                      }}
                    >
                      {conversation.user?.full_name || 'Unknown User'}
                    </Text>
                    {conversation.tags &&
                      (() => {
                        // Handle both string and array formats
                        let tagList: string[] | string = conversation.tags;
                        if (typeof tagList === 'string') {
                          // Remove brackets, quotes, and parse
                          tagList = tagList
                            .replace(/[[\]{}()'"]/g, '')
                            .split(',')
                            .map((t) => t.trim())
                            .filter((t) => t);
                        }

                        // Status colors mapping

                        if (Array.isArray(tagList) && tagList.length > 0) {
                          return tagList.map((tag, index) => {
                            // Clean individual tag from brackets and quotes
                            const cleanTag =
                              typeof tag === 'string'
                                ? tag.replace(/[[\]{}()'"]/g, '').trim()
                                : tag;

                            return cleanTag ? (
                              <AppStatusBadge
                                key={index}
                                status={cleanTag.toLowerCase()}
                                name={cleanTag.toLowerCase()}
                                size="small"
                                statusColors={statusColors}
                              />
                            ) : null;
                          });
                        }
                        return null;
                      })()}
                  </Flex>
                </Flex>
              }
              description={
                <StyledDescription
                  type="secondary"
                  style={{margin: '8px 0 0', fontSize: 13, lineHeight: 1.6}}
                  ellipsis={{
                    rows: 2,
                    expandable: false,
                  }}
                >
                  {conversation.description}
                </StyledDescription>
              }
              $radius="12px"
              style={{
                padding: '16px',
                marginBottom: '12px',
                border: '1px solid #f0f0f0',
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                background: '#ffffff',
              }}
            />
          );
        }}
      />

      <AppDrawer
        open={isDrawerOpen}
        fullWidth
        closable
        isTabDrawer
        onClose={handleDrawerClose}
        title={
          activeConversationData?.user?.full_name
            ? `Conversation with ${activeConversationData.user.full_name}`
            : activeConversationData?.title || 'Conversation'
        }
      >
        {activeConversationData && (
          <ConversationView conversation={activeConversationData}/>
        )}
      </AppDrawer>
    </>
  );
};

export default Conversations;
