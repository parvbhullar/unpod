import { Button, Space } from 'antd';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { changeDateStringFormat } from '@unpod/helpers/DateHelper';
import { localizeCallStatusLabels } from '@unpod/helpers/LocalizationFormatHelper';

export const VIEW_DATA_STATUS_FILTER = {
  pending: { color: 'badge-info', label: 'common.pending' },
  paid: { color: 'badge-success', label: 'common.paid' },
  failed: { color: 'badge-error', label: 'common.failed' },
  cancelled: { color: 'badge-warning', label: 'common.cancelled' },
  refunded: { color: 'badge-info', label: 'common.refunded' },
};

export const getColumns = (
  onDownloadInvoice: (record: any) => void,
  onPayInvoice: (record: any) => void,
  loading: boolean,
  formatMessage: (msg: any) => string,
) => {
  return [
    {
      title: formatMessage({ id: 'billing.paymentInvoiceNumber' }),
      dataIndex: 'invoice_number',
      key: 'invoice_number',
    },
    {
      title: formatMessage({ id: 'billing.paymentInvoiceDate' }),
      dataIndex: 'invoice_date',
      key: 'invoice_date',
      render: (text: any) =>
        changeDateStringFormat(
          text,
          'YYYY-MM-DD HH:mm:ss',
          'YYYY-MM-DD HH:mm:ss',
        ),
    },
    {
      title: formatMessage({ id: 'billing.paymentCost' }),
      dataIndex: 'amount',
      key: 'amount',
      render: (text: any) => getAmountWithCurrency(text || 0),
    },
    {
      title: formatMessage({ id: 'billing.paymentStatus' }),
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => (
        <AppStatusBadge
          status={status}
          name={status}
          statusColors={
            localizeCallStatusLabels(
              VIEW_DATA_STATUS_FILTER,
              formatMessage,
            ) as any
          }
        />
      ),
    },
    {
      title: formatMessage({ id: 'billing.paymentAction' }),
      dataIndex: 'action',
      key: 'action',
      align: 'center',
      render: (_text: any, record: any) => (
        <Space orientation="horizontal">
          <Button size="small" onClick={() => onDownloadInvoice(record)}>
            {formatMessage({ id: 'common.download' })}
          </Button>

          {record.status === 'pending' && (
            <Button
              size="small"
              onClick={() => onPayInvoice(record)}
              loading={loading}
            >
              {formatMessage({ id: 'common.pay' })}
            </Button>
          )}
        </Space>
      ),
    },
  ];
};
