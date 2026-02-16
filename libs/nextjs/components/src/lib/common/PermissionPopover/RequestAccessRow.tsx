import { Button, Row, Space, Typography } from 'antd';
import { useIntl } from 'react-intl';

import UserAvatar from '../UserAvatar';
import type {
  PermissionEntity,
  PermissionPopoverType,
  RequestAccessRowProps,
} from './types';

import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { maskEmail } from '@unpod/helpers/StringHelper';

const getAcceptRequestUrl = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
  member: RequestAccessRowProps['member'],
): string => {
  switch (type) {
    case 'org':
      if (member.is_member) {
        return `organization/${currentData?.domain_handle || ''}/request/${member.request_token || ''}/accept-change-role/`;
      }
      return `organization/${currentData?.domain_handle || ''}/request/${member.request_token || ''}/`;
    case 'space':
      if (member.is_member) {
        return `spaces/${currentData?.slug || ''}/request/${member.request_token || ''}/accept-change-role/`;
      }
      return `spaces/${currentData?.slug || ''}/request/${member.request_token || ''}/`;
    default:
      return `threads/${currentData?.slug || ''}/request/${member.request_token || ''}/`;
  }
};

const getRejectRequestUrl = (
  type: PermissionPopoverType,
  currentData: PermissionEntity | null | undefined,
  member: RequestAccessRowProps['member'],
): string => {
  switch (type) {
    case 'org':
      return `organization/${currentData?.domain_handle || ''}/request/${member.request_token || ''}/reject/`;
    case 'space':
      return `spaces/${currentData?.slug || ''}/request/${member.request_token || ''}/reject/`;
    default:
      return `threads/${currentData?.slug || ''}/request/${member.request_token || ''}/reject/`;
  }
};

const toErrorMessage = (error: unknown): string => {
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string') return message;
  }
  return 'Something went wrong';
};

const RequestAccessRow = ({
  type,
  currentData,
  member,
  onAcceptMemberRequest,
  onDenyMemberRequest,
}: RequestAccessRowProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const onAccessRequest = (): void => {
    const url = getAcceptRequestUrl(type, currentData, member);

    getDataApi<Partial<RequestAccessRowProps['member']>>(url, infoViewActionsContext)
      .then((response) => {
        onAcceptMemberRequest({
          ...member,
          ...(response.data || {}),
          joined: true,
        });
        infoViewActionsContext.showMessage(response.message || 'Updated');
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  const onRejectRequest = (): void => {
    const url = getRejectRequestUrl(type, currentData, member);

    getDataApi(url, infoViewActionsContext)
      .then((response) => {
        onDenyMemberRequest(member.email || member.user_email || '');
        infoViewActionsContext.showMessage(response.message || 'Updated');
      })
      .catch((error: unknown) => {
        infoViewActionsContext.showError(toErrorMessage(error));
      });
  };

  return (
    <Row justify="space-between" align="middle">
      <Space>
        <UserAvatar user={member} />
        <Space orientation="vertical" size={0}>
          {member.full_name ? (
            <Typography.Text
              type={member.joined ? undefined : 'secondary'}
              style={{ marginBottom: -4, display: 'block' }}
            >
              {member.full_name}
              {member.role === 'editor'
                ? formatMessage({ id: 'member.roleEditor' })
                : formatMessage({ id: 'member.roleViewer' })}
            </Typography.Text>
          ) : null}

          <Typography.Text type={member.joined ? undefined : 'secondary'}>
            {maskEmail(member.email || member.user_email || '')}
          </Typography.Text>
        </Space>
      </Space>

      <Space orientation="horizontal">
        <Button onClick={onAccessRequest} type="text" style={{ color: '#796CFF' }}>
          {formatMessage({ id: 'member.actionAccept' })}
        </Button>
        <Button onClick={onRejectRequest} type="text" danger>
          {formatMessage({ id: 'member.actionReject' })}
        </Button>
      </Space>
    </Row>
  );
};

export default RequestAccessRow;
