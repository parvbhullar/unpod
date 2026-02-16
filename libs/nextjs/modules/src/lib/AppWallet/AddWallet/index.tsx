import type { MouseEvent } from 'react';
import { useState } from 'react';
import { Button, Form, Radio, Space, Typography } from 'antd';
import {
  AppInputNumber,
  DrawerFooter,
  DrawerForm,
} from '@unpod/components/antd';
import { DrawerBody } from '@unpod/components/antd/AppDrawer/DrawerBody';
import { useAuthContext } from '@unpod/providers';
import AppAmountView from '@unpod/components/common/AppAmountView';
import { StyledAmountView } from '../index.styled';
import { useIntl } from 'react-intl';

const options = [
  { key: 10, value: 10, name: '+$10' },
  { key: 50, value: 50, name: '+$50' },
  { key: 100, value: 100, name: '+$100' },
];

const { Text } = Typography;
const { Item, useForm } = Form;

type AddWalletProps = {
  onWalletAddClose: () => void;
  onAddAmount: (amount: number) => void;
  loading?: boolean;
  currentBitValue: number;
  walletAmount: string;
};

const AddWallet = ({
  onWalletAddClose,
  onAddAmount,
  loading,
  currentBitValue,
  walletAmount,
}: AddWalletProps) => {
  const { formatMessage } = useIntl();
  const { currency } = useAuthContext();
  const [form] = useForm();
  const [addAmount] = useState(5);

  const onFinish = (values: { add_amount: number }) => {
    onAddAmount(values.add_amount);
  };

  const onPercentageClick = (event: MouseEvent<HTMLElement>) => {
    const value = Number((event.target as HTMLInputElement).value);
    const formValue = form.getFieldValue('add_amount');
    const finalValue = +formValue + value;
    form.setFieldsValue({
      add_amount: finalValue,
    });
  };

  const onCancel = () => {
    form.resetFields();
    onWalletAddClose();
  };

  const currentAmount = Form.useWatch('add_amount', form);
  return (
    <DrawerForm
      name="basic"
      form={form}
      initialValues={{
        add_amount: addAmount,
      }}
      onFinish={onFinish}
      autoComplete="off"
    >
      <DrawerBody>
        <Item>
          <Space>
            <Text>{formatMessage({ id: 'wallet.walletCredits' })}</Text>
            <Text>{walletAmount}</Text>
          </Space>
        </Item>
        <Item
          name="add_amount"
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'wallet.creditsError' }),
            },
          ]}
        >
          <AppInputNumber
            min={0}
            placeholder={formatMessage({ id: 'wallet.placeholder' })}
          />
        </Item>

        <StyledAmountView>
          {`${formatMessage({ id: 'wallet.amountIn' })} ${currency} :`}
          <AppAmountView
            amount={+currentAmount * currentBitValue}
            currency={currency}
          />
        </StyledAmountView>

        <Item>
          <Radio.Group>
            {options.map((item, index) => (
              <Radio.Button
                key={index}
                onClick={onPercentageClick}
                value={item.value}
              >
                {/*<Text>{getAmountWithCurrency(item.value, 'USD', 0)} Coins</Text>*/}
                <Text>+{item.value} Credits</Text>
              </Radio.Button>
            ))}
          </Radio.Group>
        </Item>
      </DrawerBody>
      <DrawerFooter>
        <Button
          onClick={onCancel}
          style={{ marginRight: 8 }}
          loading={loading}
          disabled={loading}
        >
          {formatMessage({ id: 'common.cancel' })}
        </Button>
        <Button type="primary" htmlType="submit" loading={loading}>
          {formatMessage({ id: 'wallet.addCredits' })}
        </Button>
      </DrawerFooter>
    </DrawerForm>
  );
};

export default AddWallet;
