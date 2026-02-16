import { Button, Divider, Flex, InputNumber, Space, Typography } from 'antd';
import { useState } from 'react';
import {
  StyledContainer,
  StyledContent,
  StyledRoot,
  StyledText,
} from './index.styled';
import AppTable from '@unpod/components/third-party/AppTable';
import { useIntl } from 'react-intl';

const { Text, Title } = Typography;

const AppTableAny = AppTable as any;

const Addon = ({
  setAddonOpen,
  subscription,
}: {
  setAddonOpen: (open: boolean) => void;
  subscription: any;
}) => {
  const { formatMessage } = useIntl();

  const [addons, setAddons] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {};
    const modules = (subscription as any)?.modules || [];
    modules.forEach((mod: any) => {
      initial[mod.codename] = 0;
    });
    return initial;
  });

  const data = ((subscription as any)?.modules || []).map((mod: any) => {
    let quickAdd: number[] = [];
    const rate = mod.cost;
    const valueKey = mod.codename || 0.0;

    if (mod.codename === 'voice_minutes') quickAdd = [1000, 5000, 10000];
    else if (mod.codename === 'channels' || mod.codename === 'integrations')
      quickAdd = [5, 10, 25];

    return {
      key: mod.id,
      service: mod.module_name,
      current: `${mod.allocated} ${mod.unit}${mod.allocated > 1 ? 's' : ''}`,
      rate,
      unit: `₹${rate}/${mod.unit}`,
      quickAdd,
      valueKey,
    };
  });

  const handleAddChange = (key: string, value: number | null) => {
    setAddons((prev) => ({ ...prev, [key]: value || 0 }));
  };

  const formatQuickAddLabel = (val: number) => {
    if (val >= 1000) return `${val / 1000}K`;
    return val;
  };

  const columns = [
    {
      title: formatMessage({ id: 'addon.service' }),
      dataIndex: 'service',
      key: 'service',
      render: (text: any) => <Text strong>{text}</Text>,
    },
    {
      title: formatMessage({ id: 'addon.current' }),
      dataIndex: 'current',
      key: 'current',
    },
    {
      title: formatMessage({ id: 'addon.add' }),
      key: 'add',
      render: (_: any, record: any) => (
        <InputNumber
          min={0}
          value={addons[record.valueKey as string]}
          onChange={(val) => handleAddChange(record.valueKey, val)}
          style={{ width: 80 }}
        />
      ),
    },
    {
      title: formatMessage({ id: 'addon.rate' }),
      dataIndex: 'unit',
      key: 'unit',
    },
    {
      title: formatMessage({ id: 'addon.cost' }),
      key: 'cost',
      render: (_: any, record: any) => {
        const cost = (addons[record.valueKey as string] || 0) * record.rate;
        return <Text>₹{cost.toFixed(2)}</Text>;
      },
    },
    {
      title: formatMessage({ id: 'addon.quickAdd' }),
      key: 'quickAdd',
      render: (_: any, record: any) => (
        <Space>
          {record.quickAdd.map((val: number) => (
            <Button
              key={val}
              size="small"
              onClick={() =>
                handleAddChange(
                  record.valueKey,
                  (addons[record.valueKey as string] || 0) + val,
                )
              }
            >
              +{formatQuickAddLabel(val)}
            </Button>
          ))}
        </Space>
      ),
    },
  ];

  const subtotal = data?.reduce(
    (sum: number, item: any) =>
      sum +
      Number(addons[item.valueKey as string] ?? 0) * Number(item.rate ?? 0),
    0,
  );
  const tax = subtotal * 0.18;
  const total = subtotal + tax;

  return (
    <StyledRoot>
      <AppTableAny
        rowKey={'key'}
        columns={columns}
        dataSource={data}
        pagination={false}
        bordered={false}
        size="large"
        fullHeight={400}
        style={{ blockSize: 'auto' }}
      />

      <StyledContent>
        <Title level={5}>{formatMessage({ id: 'addons.orderSummary' })}</Title>
        <Flex vertical gap={4} style={{ marginTop: 8 }}>
          {data?.map((item: any) => {
            return (
              <Flex key={item.valueKey} justify="space-between">
                <StyledText strong>
                  {(item.service ? item.service : item.valueKey)
                    .replace(/[^a-zA-Z0-9]+/g, ' ')
                    .trim()}
                  :
                </StyledText>
                <Text>
                  ₹
                  {(
                    Number(addons[item.valueKey as string] ?? 0) *
                    Number(
                      data?.find((d: any) => d.valueKey === item.valueKey)
                        ?.rate ?? 0,
                    )
                  ).toFixed(2)}
                </Text>
              </Flex>
            );
          })}

          <Flex justify="space-between">
            <Text strong>{formatMessage({ id: 'addons.subtotal' })}</Text>
            <Text strong>₹{subtotal.toFixed(2)}</Text>
          </Flex>
          <Flex justify="space-between">
            <Text>{formatMessage({ id: 'addons.taxAmount' })}</Text>
            <Text>₹{tax.toFixed(2)}</Text>
          </Flex>
          <Divider style={{ margin: '8px 0' }} />
          <Flex justify="space-between">
            <Text strong>{formatMessage({ id: 'addons.totalAmount' })}</Text>
            <Text strong>₹{total.toFixed(2)}</Text>
          </Flex>
        </Flex>
      </StyledContent>

      <StyledContainer>
        <Flex justify="end" gap={8}>
          <Button onClick={() => setAddonOpen(false)}>
            {formatMessage({ id: 'common.cancel' })}
          </Button>
          <Button type="primary">
            {formatMessage({ id: 'addons.addSubscriptionButton' })}
          </Button>
        </Flex>
      </StyledContainer>
    </StyledRoot>
  );
};

export default Addon;
