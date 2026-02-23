import AppTableActions from '../AppTableActions';
import {getActionColumn} from '@unpod/helpers/TableHelper';
import {capitalizedString} from '@unpod/helpers/StringHelper';
import type {ColumnType} from 'antd/es/table';

type SharedUser = {
  email: string;
  role_code?: string;
};

export const getColumns = (
  onDelete: (email: string) => void,
): ColumnType<SharedUser>[] => {
  const actionColumn = getActionColumn() as ColumnType<SharedUser>;

  return [
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (_: unknown, record: SharedUser) => record.email,
    },
    {
      title: 'Role',
      dataIndex: 'role_code',
      render: (_: unknown, record: SharedUser) =>
        capitalizedString(record?.role_code),
    },
    {
      ...actionColumn,
      title: 'Actions',
      dataIndex: 'file',
      render: (text: string, record: SharedUser) => (
        <AppTableActions
          key={text}
          showToolTip
          onDelete={() => onDelete(record.email)}
        />
      ),
    },
  ];
};
