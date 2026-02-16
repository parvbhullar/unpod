import { DatePicker, Input, InputNumber } from 'antd';

type AppSuperbookInputItem = {
  name?: string;
  type?: string;
  [key: string]: unknown;
};

type AppSuperbookInputsProps = {
  item: AppSuperbookInputItem;
};

const AppSuperbookInputs = ({ item }: AppSuperbookInputsProps) => {
  const placeholder = item.name || '';

  if (item.type === 'number') {
    return <InputNumber style={{ width: '100%' }} placeholder={placeholder} />;
  }

  if (item.type === 'date') {
    return <DatePicker style={{ width: '100%' }} />;
  }

  return <Input placeholder={placeholder} />;
};

export default AppSuperbookInputs;
