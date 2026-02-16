import { getActionColumn } from '@unpod/helpers/TableHelper';
import { StyledTag } from './index.styled';
import AppTableActions from '@unpod/components/common/AppTableActions';

export const getColumns = ({
  onEditClick,
  onDeleteConfirm,
  formatMessage,
}: {
  onEditClick: (record: any) => void;
  onDeleteConfirm: (record: any) => void;
  formatMessage: (msg: any) => string;
}) => {
  const AppTableActionsAny = AppTableActions as any;
  return [
    {
      title: formatMessage({ id: 'table.bridgeId' }),
      dataIndex: 'bridge_slug',
      key: 'bridge_slug',
    },
    {
      title: formatMessage({ id: 'table.provider' }),
      dataIndex: 'provider',
      key: 'provider',
    },
    {
      title: formatMessage({ id: 'table.direction' }),
      dataIndex: 'direction',
      key: 'direction',
      render: (direction: any, record: any) =>
        record.service_type === 'rule' &&
        record.provider.toLowerCase() === 'livekit'
          ? formatMessage({ id: 'table.dispatchRule' })
          : direction,
    },
    {
      title: formatMessage({ id: 'table.type' }),
      dataIndex: 'trunk_type',
      key: 'trunk_type',
    },
    {
      title: formatMessage({ id: 'table.address' }),
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: formatMessage({ id: 'table.numbers' }),
      dataIndex: 'numbers',
      key: 'numbers',
      render: (numbers: any) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(numbers || []).map((num: any, idx: number) => (
            <StyledTag key={idx} color="#f5f5f5" style={{ color: '#000' }}>
              {num}
            </StyledTag>
          ))}
        </div>
      ),
    },
    {
      title: formatMessage({ id: 'table.status' }),
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => (
        <StyledTag
          color={
            status === 'failed'
              ? '#cd201f'
              : status === 'pending'
                ? '#ff9900'
                : '#87d068'
          }
        >
          {formatMessage({ id: `table.status.${status}` })}
        </StyledTag>
      ),
    },
    {
      title: formatMessage({ id: 'table.action' }),
      dataIndex: 'created',
      key: 'created',
      ...getActionColumn(),
      render: (_text: any, record: any) => {
        const props: any = {
          showToolTip: true,
          onEdit: () => onEditClick(record),
          onDelete: () => onDeleteConfirm(record),
        };

        if (record.service_type === 'rule') {
          props.onEdit = undefined;
        }

        return <AppTableActionsAny {...props} />;
      },
    },
  ];
};
