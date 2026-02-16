export const getColumns = (formatMessage: (msg: any) => string) => {
  return [
    {
      title: formatMessage({ id: 'billing.service' }),
      dataIndex: 'serviceName',
      key: 'serviceName',
    },
    {
      title: formatMessage({ id: 'billing.allocated' }),
      dataIndex: 'allocated',
      key: 'allocated',
    },
    {
      title: formatMessage({ id: 'billing.consumed' }),
      dataIndex: 'consumed',
      key: 'consumed',
    },
    {
      title: formatMessage({ id: 'billing.remaining' }),
      dataIndex: 'remaining',
      key: 'remaining',
      render: (_text: any, record: any) => {
        if (record.allocated === '-' || record.consumed === '-') {
          return '-';
        } else if (record.extra_usage > 0) {
          return (
            <span
              style={{
                color: 'orange',
              }}
            >
              Over Used
            </span>
          );
        } else {
          return record.remaining;
        }
      },
    },

    {
      title: formatMessage({ id: 'billing.cost' }),
      dataIndex: 'cost',
      key: 'cost',
      align: 'right' as const,
    },
  ];
};
