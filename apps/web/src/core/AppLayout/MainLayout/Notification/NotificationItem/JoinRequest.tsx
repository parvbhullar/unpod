import { List, Skeleton } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { ListDate, StyledListItemWrapper } from '../Notification.styled';
import { putDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import type { NotificationItemData } from '../types';

type JoinRequestProps = {
  loading: boolean;
  item: NotificationItemData;
  updateItem: (token: string) => void;
};

const JoinRequest = ({ loading, item, updateItem }: JoinRequestProps) => {
  const infoViewContext = useInfoViewActionsContext();
  const onHandleNotification = () => {
    if (!item.read && item.token) {
      putDataApi('notifications/', infoViewContext, {
        token: item.token,
      }).then(() => updateItem(item.token as string));
    }
    switch (item.object_type) {
      // case NotificationType.Invoice: {
      //   router.push(`/invoice/detail/${item.object_id}/`);
      //   return;
      // }
      // case NotificationType.PurchaseOrder: {
      //   router.push(`/purchase-order/detail/${item.object_id}/`);
      //   return;
      // }
      default:
        return;
    }
  };
  return (
    <StyledListItemWrapper
      $isRead={item.expired || item.read}
      extra={<ListDate>{getTimeFromNow(item.created)}</ListDate>}
      onClick={onHandleNotification}
    >
      <Skeleton avatar title={false} loading={loading} active>
        <List.Item.Meta
          avatar={
            item.color?.toLowerCase() === 'green' ? (
              <CheckCircleOutlined
                style={{
                  fontSize: 16,
                  marginTop: 4,
                  color: item.color?.toLowerCase(),
                }}
              />
            ) : (
              <CloseCircleOutlined
                style={{
                  fontSize: 16,
                  marginTop: 4,
                  color: item.color?.toLowerCase(),
                }}
              />
            )
          }
          title={item.title}
          description={item.body}
        />
      </Skeleton>
    </StyledListItemWrapper>
  );
};

export default JoinRequest;
