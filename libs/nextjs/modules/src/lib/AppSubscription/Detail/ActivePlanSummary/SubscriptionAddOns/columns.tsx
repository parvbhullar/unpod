import { Button, InputNumber, Space, Typography } from 'antd';
import AppAmountView from '@unpod/components/common/AppAmountView';
import { getItemAmount } from '@unpod/helpers/CalculationHelper';

const { Text } = Typography;

const formatQuickAddLabel = (val: number) => {
  if (val >= 1000) return `${val / 1000}K`;
  return val;
};

const getQuickAddOptions = (codename: string) => {
  if (['channels', 'integrations'].includes(codename)) {
    return [5, 10, 25];
  }

  return [1000, 5000, 10000];
};

export const getColumns = (
  handleAddChange: (codename: string, val: number) => void,
  formatMessage: (msg: any) => string,
) => {
  return [
    {
      title: formatMessage({ id: 'addons.module' }),
      dataIndex: 'module_name',
      key: 'module_name',
      render: (text: any) => <Text strong>{text || '-'}</Text>,
    },
    {
      title: formatMessage({ id: 'addons.current' }),
      dataIndex: 'current',
      key: 'current',
      render: (_text: any, record: any) => (
        <Text>{`${record.allocated} ${record.unit}${
          record.allocated > 1 ? 's' : ''
        }`}</Text>
      ),
    },
    {
      title: formatMessage({ id: 'addons.add' }),
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: any, record: any) => (
        <InputNumber
          min={0}
          value={quantity}
          onChange={(val) => handleAddChange(record.codename, val)}
          style={{ width: 80 }}
        />
      ),
    },
    {
      title: formatMessage({ id: 'addons.rate' }),
      dataIndex: 'unit',
      key: 'unit',
      render: (_: any, record: any) => (
        <Text>{`₹${record.cost}/${record.unit}`}</Text>
      ),
    },
    {
      title: formatMessage({ id: 'addons.cost' }),
      key: 'cost',
      render: (_: any, record: any) => (
        <AppAmountView amount={getItemAmount(record)} />
      ),
    },
    {
      title: formatMessage({ id: 'addons.quickAdd' }),
      dataIndex: 'actions',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          {getQuickAddOptions(record.codename).map((val) => (
            <Button
              key={val}
              size="small"
              onClick={() =>
                handleAddChange(record.codename, record.quantity + val)
              }
            >
              +{formatQuickAddLabel(val)}
            </Button>
          ))}
        </Space>
      ),
    },
  ];
};
