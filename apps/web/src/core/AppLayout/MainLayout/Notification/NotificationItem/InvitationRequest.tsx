import { Button, List, Skeleton, Space } from 'antd';
import { ListDate, StyledListItemWrapper } from '../Notification.styled';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import type { NotificationItemData } from '../types';

type InvitationRequestProps = {
  item: NotificationItemData;
  loading: boolean;
  onHandleNotification: (action: string) => void;
};

const InvitationRequest = ({
  item,
  loading,
  onHandleNotification,
}: InvitationRequestProps) => {
  return (
    <StyledListItemWrapper
      $isRead={item.expired || item.read}
      extra={<ListDate>{getTimeFromNow(item.created)}</ListDate>}
    >
      <Skeleton avatar title={false} loading={loading} active>
        <List.Item.Meta title={item.title} description={item.body} />

        <Space
          direction="horizontal"
          style={{
            display: 'flex',
            width: '100%',
            justifyContent: 'flex-end',
          }}
        >
          <Button
            size="small"
            danger
            disabled={item.expired}
            onClick={() => onHandleNotification('decline')}
          >
            Reject
          </Button>
          <Button
            size="small"
            type="primary"
            ghost
            disabled={item.expired}
            onClick={() => onHandleNotification('accept')}
          >
            Accept
          </Button>
        </Space>
      </Skeleton>
    </StyledListItemWrapper>
  );
};

export default InvitationRequest;
