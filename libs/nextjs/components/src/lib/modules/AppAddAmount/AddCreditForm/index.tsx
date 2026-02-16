import { useState } from 'react';
import { Button, Form, Radio, Row, Space, Typography } from 'antd';
import AppInputNumber from '../../../antd/AppInputNumber';

const options = [
  { key: 10, value: 10, name: '+$10' },
  { key: 50, value: 50, name: '+$50' },
  { key: 100, value: 100, name: '+$100' },
];

type AddCreditFormProps = {
  onWalletAddClose: () => void;
  onAddAmount: (amount: number) => void;
  loading?: boolean;
  walletAmount?: string | number;};

const AddCreditForm = ({
  onWalletAddClose,
  onAddAmount,
  loading,
  walletAmount,
}: AddCreditFormProps) => {
  const [form] = Form.useForm();
  const [addAmount] = useState(5);

  const onFinish = (values: { add_amount: number }) => {
    onAddAmount(values.add_amount);
  };

  const onPercentageClick = (event: any) => {
    const value = +event.target.value;
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

  return (
    <Form
      name="basic"
      form={form}
      initialValues={{
        add_amount: addAmount,
      }}
      onFinish={onFinish}
      autoComplete="off"
    >
      <Form.Item>
        <Space>
          <Typography.Text>Wallet Credits:</Typography.Text>
          <Typography.Text>{walletAmount}</Typography.Text>
        </Space>
      </Form.Item>
      <Form.Item
        name="add_amount"
        rules={[
          {
            required: true,
            message: `Add Amount is Required`,
          },
        ]}
      >
        <AppInputNumber min={0} placeholder="Enter Amount" />
      </Form.Item>

      <Form.Item>
        <Radio.Group>
          {options.map((item, index) => (
            <Radio.Button
              key={index}
              onClick={onPercentageClick}
              value={item.value}
            >
              {item.name}
            </Radio.Button>
          ))}
        </Radio.Group>
      </Form.Item>

      <Row justify="space-between">
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          disabled={loading}
        >
          Add Credits
        </Button>
        <Button type="primary" disabled={loading} onClick={onCancel} ghost>
          Cancel
        </Button>
      </Row>
    </Form>
  );
};

export default AddCreditForm;
