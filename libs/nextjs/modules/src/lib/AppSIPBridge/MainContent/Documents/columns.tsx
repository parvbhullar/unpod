import { getFileName } from '@unpod/helpers/FileHelper';
import AppTableActions from '@unpod/components/common/AppTableActions';
import { getSpecialColumn } from '@unpod/helpers/TableHelper';
import { AppStatusBadge } from '@unpod/components/common/AppStatusBadge';
import { DOCUMENT_STATUS } from './constants';
import { Button } from 'antd';
import { MdOutlineFileUpload } from 'react-icons/md';
import { localizeCallStatusLabels } from '@unpod/helpers/LocalizationFormatHelper';

type FormatMessage = (descriptor: { id: string }) => string;

export const getColumns = (
  onDelete: (id: string | number) => void,
  onEdit: (payload: any) => void,
  formatMessage: FormatMessage,
) => {
  return [
    {
      title: formatMessage({ id: 'table.documentType' }),
      dataIndex: 'document_type',
      key: 'document_type',
      render: (_: any, record: any) => record.label,
    },
    {
      title: formatMessage({ id: 'table.name' }),
      dataIndex: 'file',
      key: 'file_name',
      render: (_: any, record: any) =>
        record?.file ? getFileName(record.file) : 'N/A',
    },
    {
      title: formatMessage({ id: 'table.status' }),
      dataIndex: 'status',
      render: (_: any, record: any) => {
        // Ensure status is a string key, not an object
        const statusKey =
          typeof record.status === 'string'
            ? record.status
            : record.status?.key || 'pending';

        return (
          <AppStatusBadge
            status={statusKey}
            statusColors={
              localizeCallStatusLabels(
                DOCUMENT_STATUS as any,
                formatMessage,
              ) as any
            }
          />
        );
      },
    },

    {
      title: formatMessage({ id: 'table.action' }),
      dataIndex: 'file',
      key: 'file_action',
      ...getSpecialColumn(),
      render: (text: any, record: any) =>
        record?.id ? (
          <AppTableActions
            key={text}
            showToolTip
            downloadUrl={record.file}
            onDelete={() => onDelete(record.id)}
            onEdit={() =>
              onEdit({
                document_type: record.document_type,
                key: record.key,
                title: record.label,
              })
            }
          />
        ) : (
          <Button
            type="primary"
            size="small"
            style={{
              maxHeight: 26,
              fontSize: 12,
              gap: 4,
            }}
            icon={<MdOutlineFileUpload style={{ fontSize: 18 }} />}
            onClick={() =>
              onEdit({
                document_type: record.document_type,
                key: record.key,
                title: record.label,
              })
            }
          >
            {formatMessage({ id: 'common.upload' })}
          </Button>
        ),
    },
  ];
};
