import React from 'react';
import type { FormListProps } from 'antd/es/form/FormList';
import { Button, Form, Typography } from 'antd';
import AppInput from '../../AppInput';
import { MdAdd, MdDelete } from 'react-icons/md';
import { StyledItemRow } from '../index.styled';
import { getMachineName } from '@unpod/helpers/StringHelper';

const { Paragraph } = Typography;

type FormListField = {
  title: string;
  name: string;};

export type FormListComponentProps = Omit<
  FormListProps,
  'children' | 'name'
> & {
  field: FormListField;};

const FormList: React.FC<FormListComponentProps> = ({
  field,
  ...restProps
}) => {
  const form = Form.useFormInstance();
  return (
    <>
      <Paragraph>{field.title}</Paragraph>
      <Form.List name={field.name} {...restProps}>
        {(fields, { add, remove }) => {
          return (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <StyledItemRow key={key}>
                  <Form.Item
                    {...restField}
                    name={[name, 'key']}
                    rules={[
                      {
                        required: true,
                        message: 'This field is required',
                      },
                    ]}
                  >
                    <AppInput
                      placeholder="Meta Key"
                      asterisk
                      onBlur={(event: React.FocusEvent<HTMLInputElement>) => {
                        const configKey = event.target.value;

                        if (configKey) {
                          const formattedKey = getMachineName(configKey);
                          const items = form.getFieldValue(field.name);
                          items[name].key = formattedKey;
                          form.setFieldsValue({ [field.name]: items });
                        }
                      }}
                    />
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, 'value']}
                    rules={[
                      {
                        required: true,
                        message: 'This field is required',
                      },
                    ]}
                  >
                    <AppInput placeholder="Meta Value" asterisk />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      onClick={() => remove(name)}
                      icon={<MdDelete fontSize={18} />}
                      danger
                      ghost
                    />
                  </Form.Item>
                </StyledItemRow>
              ))}
              <Form.Item>
                <Button
                  type="dashed"
                  onClick={() => add()}
                  block
                  icon={<MdAdd />}
                >
                  Add field
                </Button>
              </Form.Item>
            </>
          );
        }}
      </Form.List>
    </>
  );
};

export default FormList;
