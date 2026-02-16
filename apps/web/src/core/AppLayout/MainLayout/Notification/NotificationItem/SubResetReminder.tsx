import { List, Skeleton } from 'antd';
import { ListDate, StyledListItemWrapper } from '../Notification.styled';
import { putDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import type { NotificationItemData } from '../types';

type SubResetReminderProps = {
  loading: boolean;
  item: NotificationItemData;
  updateItem: (token: string) => void;
};

const SubResetReminder = ({
  loading,
  item,
  updateItem,
}: SubResetReminderProps) => {
  const infoViewContext = useInfoViewActionsContext();

  const onNotificationClick = () => {
    if (!item.read && item.token) {
      (
        putDataApi('notifications/', infoViewContext, {
          token: item.token,
        }) as Promise<{ message?: string }>
      )
        .then((response) => {
          updateItem(item.token as string);
          console.log(response.message);
        })
        .catch((error: { message?: string }) => {
          console.error('Error marking notification as read:', error.message);
          infoViewContext.showError('Failed to mark notification as read.');
        });
    }
  };

  return (
    <StyledListItemWrapper
      $isRead={item.expired || !item.read}
      extra={<ListDate>{getTimeFromNow(item.created)}</ListDate>}
      onClick={onNotificationClick}
    >
      <Skeleton avatar title={false} loading={loading} active>
        <List.Item.Meta title={item.title} description={item.body} />
      </Skeleton>
    </StyledListItemWrapper>
  );
};

export default SubResetReminder;
