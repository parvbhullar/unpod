import type { FormItemProps } from 'antd';
import { Form } from 'antd';
import { getFieldValidationRules } from '@unpod/helpers/FormHelper';
import { FC, ReactNode } from 'react';
import type { Rule } from 'antd/es/form';

type FormFieldProps = {
  name: string | (string | number)[];
  required?: boolean;
  label?: string;
  rules?: Rule[];};

export type FormItemComponentProps = Omit<
  FormItemProps,
  'name' | 'rules' | 'children'
> & {
  field: FormFieldProps;
  children: ReactNode;};

export const FormItem: FC<FormItemComponentProps> = ({
  field,
  children,
  ...restProps
}) => {
  return (
    <Form.Item
      name={field.name}
      rules={getFieldValidationRules(field) as Rule[]}
      {...restProps}
    >
      {children}
    </Form.Item>
  );
};

export default FormItem;
