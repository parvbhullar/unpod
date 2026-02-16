import React, { ReactNode, useEffect, useMemo } from 'react';
import { useGetDataApi } from '@unpod/providers';
import { Button, Flex, Form, Space, Spin } from 'antd';
import { isPlainObject } from 'lodash';
import FormItem from './FormItem';
import FormControl from './FormControl';
import FormList from './FormList';
import {
  FieldDependency,
  isFieldDependencyResolved,
} from '@unpod/helpers/FormHelper';
import { useIntl } from 'react-intl';
import { FormInstance } from 'antd/es/form';

type FormField = {
  id: string | number;
  type: string;
  name?: string | (string | number)[];
  title?: string;
  dependencies?: FieldDependency[];
  [key: string]: unknown;};

const getFieldComponent = (field: FormField) => {
  if (field.type === 'json') {
    if (!field.name || !field.title) return null;
    return (
      <FormList
        key={field.id}
        field={{ name: field.name as string, title: field.title }}
      />
    );
  }
  if (!field.name) return null;
  return (
    <FormItem key={field.id} field={{ ...field, name: field.name }}>
      <FormControl field={field} />
    </FormItem>
  );
};

type AppFormProps = {
  formSlug: string;
  form?: FormInstance;
  onFinish: (values: any) => void;
  children?: ReactNode;
  submitBtnText?: string;
  resetBtn?: boolean;
  formLayout?: 'vertical' | 'horizontal' | 'inline';
  loading?: boolean;
  renderFormItem?: (field: FormField, formItem: ReactNode) => ReactNode;
  onCancel?: () => void;
  initialValues?: any;};

const AppForm: React.FC<AppFormProps> = ({
  formSlug,
  form: externalForm,
  onFinish,
  children,
  submitBtnText = 'Submit',
  resetBtn = false,
  formLayout = 'vertical',
  loading = false,
  renderFormItem,
  onCancel,
  initialValues,
}) => {
  const { formatMessage } = useIntl();
  const [{ apiData, loading: formLoading }] = useGetDataApi<{
    form_fields?: FormField[];
  }>(`dynamic-forms/${formSlug}/`, { data: { form_fields: [] } });
  const [internalForm] = Form.useForm();
  const form = externalForm || internalForm;

  useEffect(() => {
    if (initialValues && isPlainObject(initialValues)) {
      form.setFieldsValue(initialValues);
    }
  }, [initialValues, form, formLoading]);

  const formFields = useMemo(() => {
    const formData = apiData?.data || { form_fields: [] };
    if (formData?.form_fields?.length === 0) {
      return null;
    }
    const fieldItems: ReactNode[] = [];
    formData?.form_fields?.forEach((field: FormField, index: number) => {
      let formItem: ReactNode | null = null;
      if (field?.dependencies?.length) {
        formItem = (
          <Form.Item
            noStyle
            key={`${field.id}-${index}`}
            dependencies={field?.dependencies?.map((item) => item.depends_on)}
          >
            {({ getFieldValue }) =>
              isFieldDependencyResolved(field.dependencies ?? [], getFieldValue)
                ? getFieldComponent(field)
                : null
            }
          </Form.Item>
        );
      } else {
        formItem = getFieldComponent(field);
      }

      if (renderFormItem && typeof renderFormItem === 'function') {
        formItem = renderFormItem(field, formItem);
      }
      if (formItem) fieldItems.push(formItem);
    });
    return fieldItems;
  }, [apiData, renderFormItem]);

  if (formLoading) {
    return <Spin spinning={formLoading} size="small" />;
  }
  return (
    <Form
      autoComplete="off"
      form={form}
      layout={formLayout}
      onFinish={onFinish}
    >
      {formFields || <p>{formatMessage({ id: 'form.fieldsDes' })}</p>}
      <Flex justify={'flex-end'}>
        {!formLoading &&
          (children ? (
            children
          ) : (
            <Space size={'middle'}>
              {onCancel && (
                <Button onClick={onCancel}>
                  {formatMessage({ id: 'common.cancel' })}
                </Button>
              )}
              <Button
                type="primary"
                htmlType="submit"
                disabled={loading}
                loading={loading}
              >
                {submitBtnText}
              </Button>
              {resetBtn && (
                <Button htmlType="reset" onClick={() => form.resetFields()}>
                  {formatMessage({ id: 'common.reset' })}
                </Button>
              )}
            </Space>
          ))}
      </Flex>
    </Form>
  );
};

export default AppForm;
