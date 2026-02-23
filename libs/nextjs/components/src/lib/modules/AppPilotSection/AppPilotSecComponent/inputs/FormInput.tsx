import type {ReactElement} from 'react';
import {Fragment} from 'react';

import {Button, Form, Typography} from 'antd';
import {INPUT_COMPONENTS, InputText} from './components';
import {StyledRow, StyledTitle} from './index.styled';
import {MdAdd} from 'react-icons/md';
import {useIntl} from 'react-intl';

const {Item, List, ErrorList} = Form;
const {Paragraph} = Typography;

type InputField = {
  type: string;
  name?: string;
  title?: string;
  placeholder?: string;
  required?: boolean;
  description?: string;
  config?: { attributes?: Record<string, any> };
  [key: string]: any;
};

const FormItem = ({name, field}: { name: string; field: InputField }) => {
  const InputComponent =
    (INPUT_COMPONENTS as Record<string, (props: any) => ReactElement>)[
      field.type
      ] || InputText;
  const attributes = field?.config?.attributes || {};

  return (
    <Item
      name={name}
      rules={[
        {
          required: field.required,
          message: `${field.title} is required`,
        },
      ]}
      {...attributes}
    >
      <InputComponent field={field}/>
    </Item>
  );
};

const FormItemList = ({name, field}: { name: string; field: InputField }) => {
  const {formatMessage} = useIntl();

  const InputComponent =
    (INPUT_COMPONENTS as Record<string, (props: any) => ReactElement>)[
      field.type
      ] || InputText;

  return (
    <List
      name={name}
      rules={[
        {
          validator: async (_, value) => {
            if (field.required && (!value || value.length === 0)) {
              return Promise.reject(
                new Error(
                  formatMessage(
                    {id: 'formItem.errorMessage'},
                    {title: field.title},
                  ),
                ),
              );
            }
            return Promise.resolve();
          },
        },
      ]}
    >
      {(fields, {add, remove}, {errors}) => (
        <Fragment>
          <InputComponent field={field} fields={fields} remove={remove}/>

          <Item>
            <ErrorList errors={errors}/>

            <Button type="dashed" onClick={() => add()} block icon={<MdAdd/>}>
              {field.placeholder
                ? field.placeholder
                : formatMessage({id: 'common.addItem'})}
            </Button>
          </Item>
        </Fragment>
      )}
    </List>
  );
};

const FormInput = ({
                     component,
                     field,
                   }: {
  component: { slug?: string; name?: string };
  field: InputField;
}) => {
  const slug = component.slug || component.name || '';
  const name = `${slug}__${field.name}`;

  return (
    <Fragment>
      {field.placeholder && field.title && (
        <StyledRow>
          <StyledTitle strong>{field.title}</StyledTitle>
        </StyledRow>
      )}

      {field.description && (
        <Paragraph type="secondary">
          <div dangerouslySetInnerHTML={{__html: field.description || ''}}/>
        </Paragraph>
      )}

      {field.type === 'repeater' ? (
        <FormItemList name={name} field={field}/>
      ) : (
        <FormItem name={name} field={field}/>
      )}
    </Fragment>
  );
};

export default FormInput;
