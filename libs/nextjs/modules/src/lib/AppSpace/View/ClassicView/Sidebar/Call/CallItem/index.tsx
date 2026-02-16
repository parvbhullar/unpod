import { Flex, Typography } from 'antd';
import clsx from 'clsx';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import {
  StyledHeaderExtra,
  StyledInnerRoot,
  StyledItem,
  StyledListHeader,
  StyledMeta,
  StyledParagraph,
  StyledRoot,
} from './index.styled';
import { useRouter } from 'next/navigation';
import {
  MdCallMade,
  MdCallReceived,
  MdCancel,
  MdError,
  MdPhone,
  MdPhoneMissed,
} from 'react-icons/md';
import { IoCalendarOutline } from 'react-icons/io5';
import UserAvatar from '@unpod/components/common/UserAvatar';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { useIntl } from 'react-intl';
import type { Call } from '@unpod/constants/types';

const { Title } = Typography;

dayjs.extend(utc);

type CallItemProps = {
  data: Call;
};

const CallItem = ({ data }: CallItemProps) => {
  const { setActiveCall, setDocumentMode, setSelectedDocs } =
    useAppSpaceActionsContext();
  const { activeCall, activeTab, currentSpace, selectedDocs } =
    useAppSpaceContext();
  const { formatMessage } = useIntl();
  const activeCallData = activeCall as Call | null;
  const selectedDocIds = (selectedDocs as Array<string | number>) ?? [];

  const router = useRouter();

  // Format time WhatsApp style (convert UTC to local timezone)
  const getFormattedTime = (timestamp?: string) => {
    if (!timestamp) return '';

    // Parse as UTC and convert to local timezone
    const callTime = dayjs.utc(timestamp).local();
    const now = dayjs();
    const yesterday = now.subtract(1, 'day');

    if (callTime.isSame(now, 'day')) {
      // Today: show time in local timezone
      return callTime.format('HH:mm');
    } else if (callTime.isSame(yesterday, 'day')) {
      // Yesterday
      return formatMessage({ id: 'day.yesterday' });
    } else if (callTime.isSame(now, 'year')) {
      // This year: show month and day
      return callTime.format('MMM DD');
    } else {
      // Different year: show full date
      return callTime.format('DD/MM/YY');
    }
  };

  // Extract phone number based on call type and status
  const getPhoneNumber = () => {
    // If status is in_progress, use input.contact_number
    if (data?.status === 'in_progress' && data?.input?.contact_number) {
      return data.input.contact_number;
    }
    if (data?.status === 'completed') {
      // If call type is inbound, use output.customer
      if (data?.output?.call_type === 'inbound' && data?.output?.customer) {
        return data.output.customer;
      }
      // If call type is inbound, use output.customer
      if (data?.output?.call_type === 'outbound') {
        return data.input?.contact_number
          ? data.input.contact_number
          : data.output.customer;
      }
    }
    return data?.input?.contact_number;
  };

  // Extract phone number based on call type and status
  const getCustomerName = () => {
    return data?.input?.name?.startsWith('sip') ? '' : data?.input?.name;
  };

  const phoneNumber = getPhoneNumber();
  const phoneName = getCustomerName();
  const callType = data?.output?.call_type || data?.input?.call_type;
  const isInbound = callType === 'inbound';
  const callStatus = data?.output?.call_status
    ? data?.output?.call_status
    : data?.status;
  const isMissedCall =
    callStatus === 'notConnected' ||
    callStatus === 'cancelled' ||
    callStatus === 'failed';
  const formattedTime = getFormattedTime(data?.created || data?.modified);

  const getStatusColor = () => {
    switch (callStatus) {
      case 'notConnected':
        return '#ff4d4f'; // Red - missed call
      case 'failed':
        return '#cf1322'; // Dark red - error
      case 'cancelled':
        return '#fa8c16'; // Orange - cancelled
      case 'completed':
        return '#52c41a'; // Green - success
      case 'connected':
        return '#1890ff'; // Blue - in progress
      case 'scheduled':
        return '#1890ff'; // Blue - scheduled
      default:
        return ''; // Default text color
    }
  };

  // Get icon based on call status
  const getCallIcon = () => {
    switch (callStatus) {
      case 'connected':
        return <MdPhone size={14} />;
      case 'completed':
        return isInbound ? (
          <MdCallReceived size={14} />
        ) : (
          <MdCallMade size={14} />
        );
      case 'notConnected':
        return isInbound ? (
          <MdPhoneMissed size={14} />
        ) : (
          <MdCallMade size={14} />
        );
      case 'failed':
        return <MdError size={14} />;
      case 'cancelled':
        return <MdCancel size={14} />;
      case 'scheduled':
        return <IoCalendarOutline size={14} />;
      default:
        // Fallback to inbound/outbound icons
        return isInbound ? (
          <MdCallReceived size={14} />
        ) : (
          <MdCallMade size={14} />
        );
    }
  };

  const onClick = () => {
    if (!currentSpace?.slug || !data.task_id) return;
    setActiveCall(data as any);
    setSelectedDocs([data.task_id]);
    router.replace(`/spaces/${currentSpace.slug}/${activeTab}/${data.task_id}`);
    setDocumentMode('view');
  };

  return (
    <>
      <StyledRoot
        className={clsx('call-item', {
          active: activeCallData?.task_id === data.task_id,
          selected: selectedDocIds.includes(data.task_id as string | number),
        })}
        onClick={onClick}
      >
        <StyledItem>
          <UserAvatar
            user={{ full_name: phoneName || phoneNumber }}
            size={36}
          />
        </StyledItem>

        <StyledInnerRoot>
          <StyledListHeader>
            <StyledMeta $missed={isMissedCall}>
              <Title level={5} ellipsis>
                {phoneName || phoneNumber || 'Unknown Caller'}
              </Title>
            </StyledMeta>
            {formattedTime && (
              <StyledHeaderExtra>
                <Typography.Text type="secondary">
                  {formattedTime}
                </Typography.Text>
              </StyledHeaderExtra>
            )}
          </StyledListHeader>

          {phoneNumber && (
            <Flex
              align="center"
              gap={4}
              style={{ marginTop: -6, color: getStatusColor() }}
            >
              {getCallIcon()}
              {phoneName ? (
                <StyledParagraph
                  $missed={isMissedCall}
                  className="mb-0"
                  ellipsis
                >
                  {phoneNumber}
                </StyledParagraph>
              ) : (
                <StyledParagraph
                  $missed={isMissedCall}
                  className="mb-0"
                  ellipsis
                >
                  {isInbound
                    ? formatMessage({ id: 'call.incoming' })
                    : formatMessage({ id: 'call.outgoing' })}
                </StyledParagraph>
              )}
            </Flex>
          )}
        </StyledInnerRoot>
      </StyledRoot>
    </>
  );
};

export default CallItem;
