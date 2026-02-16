import React from 'react';
import { Typography } from 'antd';
import ApiKeyCell from '@/modules/Profile/ApiKey/ApiKeyCell';
import { changeDateStringFormat } from '@unpod/helpers/DateHelper';
import AppTableActions from '@unpod/components/common/AppTableActions';
import { getActionColumn } from '@unpod/helpers/TableHelper';
import { useIntl } from 'react-intl';

type ApiKeyRow = {
  key?: string;
  created?: string;
};

const { Text } = Typography;

export const getApiColumns = (onDelete: (key: string) => void) => {
  const { formatMessage } = useIntl();

  return [
    {
      title: formatMessage({ id: 'apiKey.title' }),
      dataIndex: 'key',
      key: 'key',
      render: (text: string) => <ApiKeyCell keyValue={text} />,
    },
    {
      title: formatMessage({ id: 'apiKey.created' }),
      dataIndex: 'created',
      key: 'created',
      render: (text: string) => (
        <Text>{changeDateStringFormat(text, 'YYYY-MM-DD HH:mm:ss')}</Text>
      ),
    },
    {
      title: formatMessage({ id: 'apiKey.actions' }),
      dataIndex: 'actions',
      key: 'actions',
      ...getActionColumn(),
      render: (_: unknown, record: ApiKeyRow) => (
        <AppTableActions
          onDelete={() => onDelete(record.key || '')}
          showToolTip
        />
      ),
    },
  ];
};
