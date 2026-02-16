import { Empty } from 'antd';
import { useIntl } from 'react-intl';
import { TableProps } from 'antd/es/table';
import { AppDataGrid } from '@unpod/react-data-grid';

type AppTableProps<T> = TableProps<T> & {
  image?: string;
  description?: string;
  [key: string]: unknown;
};

const AppTable = <T extends object>(props: AppTableProps<T>) => {
  const { formatMessage } = useIntl();
  return (
    <AppDataGrid
      bordered
      rowKey="id"
      scroll={{ x: 'auto' }}
      locale={{
        emptyText: (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={formatMessage({ id: 'peopleSummary.noDataFound' })}
          />
        ),
      }}
      {...props}
    />
  );
};

export default AppTable;
