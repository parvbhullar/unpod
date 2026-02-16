import { useEffect } from 'react';
import { Button, Form, Radio, Select, Typography } from 'antd';
import ModalWindow from '../ModalWindow';
import { StyledRoot } from './index.style';
import { AppInput } from '../AppInput';
import { AppSelect } from '../AppSelect';
import { getMachineName } from '../../helpers/StringHelper';

const { useForm } = Form;
const { Paragraph } = Typography;

type ColumnDataType = {
  label: string;
  value: string;
};

const dataTypes: ColumnDataType[] = [
  { label: 'String', value: 'text' },
  { label: 'Number', value: 'number' },
  { label: 'Date', value: 'date' },
  { label: 'Time', value: 'time' },
  { label: 'Datetime', value: 'datetime' },
];

type Props = {
  onCancel: () => void;
  columns: readonly any[];
  idx: number;
  onAddColumn: (data: any) => void;
  [key: string]: any;
};

const NewColumnWindow = ({
  onCancel,
  columns,
  idx,
  onAddColumn,
  ...restProps
}: Props) => {
  const [form] = useForm();

  useEffect(() => {
    if (idx >= 0) {
      form.setFieldsValue({ idx: idx.toString() });
    }
  }, [idx, form]);

  const onFinish = (data: any) => {
    const payload = {
      title: data.title,
      column_key: data.column_key,
      data_type: data.data_type,
      idx: data.position === 'before' ? +data.idx - 1 : +data.idx,
    };

    form.resetFields();
    onAddColumn(payload);
  };

  return (
    <ModalWindow
      title="Add Column"
      onCancel={onCancel}
      maskClosable={false}
      footer={null}
      width={320}
      centered
      {...restProps}
    >
      <StyledRoot>
        <Form
          initialValues={{ idx: idx.toString(), position: 'after' }}
          form={form}
          onFinish={onFinish}
        >
          <Form.Item
            name="title"
            rules={[
              {
                required: true,
                message: 'This is required field',
              },
            ]}
          >
            <AppInput
              placeholder="Column Title"
              onBlur={(event) => {
                const columnName = event.target.value;

                if (columnName) {
                  const column_key = getMachineName(columnName);

                  form.setFieldsValue({ column_key });
                }
              }}
            />
          </Form.Item>

          <Form.Item
            name="column_key"
            rules={[
              {
                required: true,
                message: 'This is required field',
              },
              () => ({
                validator(_, columnKey) {
                  if (columnKey) {
                    const isExists = columns.find(
                      (column) => column.dataIndex === columnKey,
                    );

                    if (isExists) {
                      return Promise.reject(
                        new Error('Column key is already exists'),
                      );
                    }
                  }

                  return Promise.resolve();
                },
              }),
            ]}
          >
            <AppInput placeholder="Column Key" />
          </Form.Item>

          <Form.Item
            name="data_type"
            rules={[
              {
                required: true,
                message: 'This is required field',
              },
            ]}
          >
            <AppSelect placeholder="Data Type">
              {dataTypes.map((type) => (
                <Select.Option key={type.value} value={type.value}>
                  {type.label}
                </Select.Option>
              ))}
            </AppSelect>
          </Form.Item>

          <Paragraph>Column Position</Paragraph>
          <Form.Item name="position">
            <Radio.Group>
              <Radio value="after"> After </Radio>
              <Radio value="before"> Before </Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="idx"
            rules={[
              {
                required: true,
                message: 'This is required field',
              },
            ]}
          >
            <AppSelect placeholder="Select Column">
              {columns.map((column, index) => (
                <Select.Option key={index} value={index.toString()}>
                  {column.title}
                </Select.Option>
              ))}
            </AppSelect>
          </Form.Item>

          <Button type="primary" htmlType="submit" block>
            Save
          </Button>
        </Form>
      </StyledRoot>
    </ModalWindow>
  );
};

export default NewColumnWindow;
