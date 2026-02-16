'use client';
import { List, Skeleton } from 'antd';
import {
  postDataApi,
  putDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import JoinRequest from './JoinRequest';
import InvitationRequest from './InvitationRequest';
import SubResetReminder from './SubResetReminder';
import AllowCancelAction from './AllowCancelAction';
import { ListDate, StyledListItemWrapper } from '../Notification.styled';
import type { NotificationItemData } from '../types';

type NotificationItemProps = {
  loading: boolean;
  item: NotificationItemData;
  updateItem: (token: string) => void;
};

const NotificationItem = ({
  loading,
  item,
  updateItem,
}: NotificationItemProps) => {
  const infoViewContext = useInfoViewActionsContext();
  const { updateAuthUser, setActiveOrg } = useAuthActionsContext();
  const { user } = useAuthContext();
  const router = useRouter();

  const onHandleNotificationRead = () => {
    if (!item.read && item.token) {
      putDataApi('notifications/', infoViewContext, {
        token: item.token,
      }).then(() => updateItem(item.token as string));
    }
    switch (item.event) {
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

  const onHandleNotification = (action: string) => {
    postDataApi<any>(`notifications/${item.token}/`, infoViewContext, {
      action: action,
    })
      .then((data) => {
        infoViewContext.showMessage(data.message || 'Updated');
        if (item.token) updateItem(item.token);
        if (action === 'accept') {
          const organizationList = [...(user?.organization_list || [])];
          if (
            !organizationList.find(
              (org) =>
                org.domain_handle ===
                (item.object_type === 'organization'
                  ? data.data.domain_handle
                  : data.data.organization.domain_handle),
            )
          ) {
            const organization =
              item.object_type === 'organization'
                ? data.data
                : data.data.organization;
            organizationList.push(organization);
          }
          updateAuthUser({
            ...(user || {}),
            organization_list: organizationList,
          });
          setActiveOrg(
            item.object_type === 'organization'
              ? data.data
              : data.data.organization,
          );
          if (item.object_type === 'space') {
            router.push(`/spaces/${data.data.slug}`);
          } else if (item.object_type === 'organization') {
            router.push(`/org`);
          } else if (item.object_type === 'post') {
            const slug = item.event_data?.slug;
            if (slug) router.push(`/${item.object_type}/${slug}`);
          }
        }
      })
      .catch((err: { data?: { expired?: boolean }; message?: string }) => {
        if (err.data?.expired && item.token) {
          updateItem(item.token);
        }

        infoViewContext.showError(err.message || 'Failed to update');
      });
  };

  const getNotificationItem = () => {
    switch (item.event) {
      case 'invitation':
        return (
          <InvitationRequest
            item={item}
            loading={loading}
            onHandleNotification={onHandleNotification}
          />
        );
      case 'JoinRequest':
        return (
          <JoinRequest item={item} loading={loading} updateItem={updateItem} />
        );
      case 'subscription_reset_reminder':
        return (
          <SubResetReminder
            item={item}
            loading={loading}
            updateItem={updateItem}
          />
        );
      case 'allow_cancel_action':
        return (
          <AllowCancelAction
            item={item}
            loading={loading}
            updateItem={updateItem}
          />
        );
      default:
        return (
          <StyledListItemWrapper
            $isRead={item.expired || item.read}
            extra={<ListDate>{getTimeFromNow(item.created)}</ListDate>}
            onClick={onHandleNotificationRead}
          >
            <Skeleton avatar title={false} loading={loading} active>
              <List.Item.Meta
                // onClick={onHandleNotificationRead}
                title={item.title}
                description={item.description || item.body}
              />
            </Skeleton>
          </StyledListItemWrapper>
        );
    }
  };

  return getNotificationItem();
};

export default NotificationItem;
