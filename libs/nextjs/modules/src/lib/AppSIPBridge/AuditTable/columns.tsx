import { formatSecToTime, getFormattedDate } from '@unpod/helpers/DateHelper';
import { CALL_STATUS } from '@unpod/constants/BridgeConst';
import { capitalizedString } from '@unpod/helpers/StringHelper';
import {
  getColumnDateTimeProps,
  getColumnSearchProps,
  getColumnSelectBoxProps,
  onSortOrder,
} from '@unpod/helpers/TableHelper';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { localizeCallStatusLabels } from '@unpod/helpers/LocalizationFormatHelper';

export const callStatusArray = [
  {
    id: 'completed',
    name: 'Completed',
  },
  {
    id: 'success',
    name: 'Success',
  },
  {
    id: 'ANSWERED',
    name: 'Answered',
  },
  {
    id: 'FAILURE',
    name: 'Failure',
  },
  {
    id: 'failed',
    name: 'Failed',
  },
  {
    id: 'REJECTED',
    name: 'Rejected',
  },
  {
    id: 'ANSWERED',
    name: 'Answered',
  },
];

export const callTypeArray = [
  {
    id: 'inbound',
    name: 'Inbound',
  },
  {
    id: 'outbound',
    name: 'Outbound',
  },
];

type FormatMessage = (descriptor: { id: string }) => string;

export const getColumns = (formatMessage: FormatMessage) => {
  const callDetailsLabels = {
    bridgeName: formatMessage({ id: 'common.bridgeName' }),
    callType: formatMessage({ id: 'common.callType' }),
    callingNumber: formatMessage({ id: 'common.callingNumber' }),
    customerNumber: formatMessage({ id: 'common.customerNumber' }),
    callStartTime: formatMessage({ id: 'common.callStartTime' }),
    callEndTime: formatMessage({ id: 'common.callEndTime' }),
    duration: formatMessage({ id: 'common.duration' }),
    status: formatMessage({ id: 'common.status' }),
    endReason: formatMessage({ id: 'common.endReason' }),
  };

  return [
    {
      title: formatMessage({ id: 'callLogs.callId' }),
      dataIndex: 'id',
    },
    {
      title: callDetailsLabels.bridgeName,
      dataIndex: 'bridge',
      ...getColumnSearchProps(
        callDetailsLabels.bridgeName,
        'bridge__name',
        formatMessage,
      ),
      render: (_: any, item: any) => item?.bridge?.name,
    },
    {
      title: callDetailsLabels.callType,
      dataIndex: 'call_type',
      ...getColumnSelectBoxProps(
        callDetailsLabels.callType,
        'call_type',
        callTypeArray,
        formatMessage,
      ),
      render: (text: any) => capitalizedString(text),
    },
    {
      title: callDetailsLabels.callingNumber,
      dataIndex: 'source_number',
      ...getColumnSearchProps(
        callDetailsLabels.callingNumber,
        'source_number',
        formatMessage,
      ),
    },
    {
      title: callDetailsLabels.customerNumber,
      dataIndex: 'destination_number',
      ...getColumnSearchProps(
        callDetailsLabels.customerNumber,
        'destination_number',
        formatMessage,
      ),
    },
    {
      title: callDetailsLabels.callStartTime,
      dataIndex: 'start_time',
      sorter: (a: any, b: any) => onSortOrder(a, b, 'start_time', 'string'),
      ...getColumnDateTimeProps(
        callDetailsLabels.callStartTime,
        'start_time',
        formatMessage,
      ),
      render: (text: any) => getFormattedDate(text, 'DD-MM-YY HH:mm:ss'),
    },
    {
      title: callDetailsLabels.callEndTime,
      dataIndex: 'end_time',
      sorter: (a: any, b: any) => onSortOrder(a, b, 'end_time', 'string'),
      ...getColumnDateTimeProps(
        callDetailsLabels.callEndTime,
        'end_time',
        formatMessage,
      ),
      render: (text: any) => getFormattedDate(text, 'DD-MM-YY HH:mm:ss'),
    },
    {
      title: callDetailsLabels.duration,
      dataIndex: 'call_duration',
      sorter: (a: any, b: any) => onSortOrder(a, b, 'call_duration', 'string'),
      ...getColumnSearchProps(
        callDetailsLabels.duration,
        'call_duration',
        formatMessage,
      ),
      render: (text: any) => {
        return typeof text === 'number' ? `${formatSecToTime(text)}` : text;
      },
    },
    {
      title: callDetailsLabels.status,
      dataIndex: 'call_status',
      ...getColumnSelectBoxProps(
        callDetailsLabels.status,
        'call_status',
        callStatusArray,
        formatMessage,
      ),
      render: (text: any) => {
        return (
          <AppStatusBadge
            status={text || 'failed'}
            statusColors={
              localizeCallStatusLabels(CALL_STATUS as any, formatMessage) as any
            }
          />
        );
      },
    },
    {
      title: callDetailsLabels.endReason,
      dataIndex: 'end_reason',
      ...getColumnSearchProps(
        callDetailsLabels.endReason,
        'end_reason',
        formatMessage,
      ),
      // render: (text: any) => CALL_END_REASONS?.[text]?.label,
    },
    // {
    //   title: 'Provider',
    //   dataIndex: 'agent',
    //   ...getColumnSearchProps('Provider', 'agent'),
    //   render: (_, item) => item?.agent?.name,
    // },
  ];
};
