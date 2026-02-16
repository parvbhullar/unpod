import { Button, List, Skeleton, Space } from 'antd';
import { ListDate, StyledListItemWrapper } from '../Notification.styled';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import {
  getDataApi,
  postDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import type { NotificationItemData } from '../types';

type ActionRequest = {
  url?: string;
  method?: string;
  payload?: unknown;
  label?: string;
};

type AllowCancelActionProps = {
  item: NotificationItemData;
  loading: boolean;
  updateItem: (token: string) => void;
};

const AllowCancelAction = ({
  item,
  loading,
  updateItem,
}: AllowCancelActionProps) => {
  const infoViewContext = useInfoViewActionsContext();
  const eventData = item.event_data as
    | { allow_request?: ActionRequest; cancel_request?: ActionRequest }
    | undefined;
  const { allow_request = {}, cancel_request = {} } = eventData || {};

  const markAsReadAndExpired = () => {
    if (!item.read && !item.expired && item.token) {
      getDataApi(`notifications/${item.token}/expire/`, infoViewContext, {
        token: item.token,
      })
        .then(() => updateItem(item.token as string))
        .catch((error: { message?: string }) => {
          infoViewContext.showError(
            error.message || `Failed to mark notification as read.`,
          );
        });
    }
  };

  const onCancelClick = () => {
    const reqDataApi =
      allow_request?.method === 'POST' ? postDataApi : getDataApi;

    if (!cancel_request.url) return;
    const data = (allow_request?.payload ?? {}) as Record<string, unknown>;
    (
      reqDataApi(cancel_request.url, infoViewContext, data) as Promise<{
        message?: string;
      }>
    )
      .then((data) => {
        infoViewContext.showMessage(data.message || 'Updated');

        markAsReadAndExpired();
      })
      .catch((error: { message?: string }) => {
        infoViewContext.showError(
          error.message ||
            `Failed to send ${allow_request?.label || 'Accept'} request.`,
        );
      });
  };

  const onAllowClick = () => {
    const reqDataApi =
      allow_request?.method === 'POST' ? postDataApi : getDataApi;

    if (!allow_request.url) return;
    const data = (allow_request?.payload ?? {}) as Record<string, unknown>;
    (
      reqDataApi(allow_request.url, infoViewContext, data) as Promise<{
        message?: string;
      }>
    )
      .then((data) => {
        infoViewContext.showMessage(data.message || 'Updated');

        markAsReadAndExpired();
      })
      .catch((error: { message?: string }) => {
        infoViewContext.showError(
          error.message ||
            `Failed to send ${allow_request?.label || 'Accept'} request.`,
        );
      });
  };

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
            disabled={item.expired || item.read}
            onClick={onCancelClick}
          >
            {cancel_request?.label || 'Cancel'}
          </Button>
          <Button
            size="small"
            type="primary"
            ghost
            disabled={item.expired || item.read}
            onClick={onAllowClick}
          >
            {allow_request?.label || 'Accept'}
          </Button>
        </Space>
      </Skeleton>
    </StyledListItemWrapper>
  );
};

export default AllowCancelAction;
