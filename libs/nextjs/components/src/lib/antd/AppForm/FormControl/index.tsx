import {Select} from 'antd';

import AppInput from '../../AppInput';
import AppInputNumber from '../../AppInputNumber';
import AppSelect from '../../AppSelect';
import AppTextArea from '../../AppTextArea';
import AppDate from '../../AppDate';
import AppDateTime from '../../AppDateTime';
import AppTime from '../../AppTime';
import AppPassword from '../../AppPassword';
import AppSelectApi from '../../AppSelectApi';

const {Option} = Select;

type FormApiOptions = {
  endpoint?: string;
  params?: Record<string, unknown>;
  value_key?: string;
  label_key?: string;
};

type FormField = {
  title?: string;
  name?: string | (string | number)[];
  required?: boolean;
  type?: string;
  placeholder?: string;
  options?: Record<string, string | number>;
  options_type?: 'api' | string;
  options_api?: FormApiOptions;
  [key: string]: unknown;
};

type FormControlProps = {
  field: FormField;
  [key: string]: unknown;
};

const FormControl = ({field, ...rest}: FormControlProps) => {
  const {type, options, title} = field;
  if (field.required) {
    rest.asterisk = true;
  }
  const placeholderText = field?.placeholder ?? title ?? '';

  switch (type) {
    case 'text':
    case 'email':
    case 'tel':
    case 'url':
      return (
        <AppInput autoComplete="off" placeholder={placeholderText} {...rest} />
      );
    case 'range':
      return <AppInputNumber placeholder={placeholderText} {...rest} />;
    case 'select':
      return field?.options_type === 'api' ? (
        <AppSelectApi
          placeholder={placeholderText}
          apiEndpoint={field?.options_api?.endpoint || ''}
          params={field?.options_api?.params || {}}
          transform={(item: unknown) => {
            const record = item as Record<string, unknown>;
            const valueKey = field?.options_api?.value_key ?? 'id';
            const labelKey = field?.options_api?.label_key ?? 'name';
            const rawValue = record?.[valueKey] ?? record?.id;
            const value =
              typeof rawValue === 'number' || typeof rawValue === 'string'
                ? rawValue
                : String(rawValue ?? '');
            return {
              value,
              label: String(record?.[labelKey] ?? record?.name ?? ''),
            };
          }}
          {...rest}
        />
      ) : (
        <AppSelect placeholder={placeholderText} {...rest}>
          {options &&
            Object.entries(options).map(([key, value]) => (
              <Option key={key} value={value}>
                {String(value)}
              </Option>
            ))}
        </AppSelect>
      );
    case 'textarea':
      return <AppTextArea rows={5} placeholder={placeholderText} {...rest} />;
    case 'date':
      return <AppDate placeholder={placeholderText} {...rest} />;
    case 'datetime':
      return <AppDateTime placeholder={placeholderText} {...rest} />;
    case 'time':
      return <AppTime placeholder={placeholderText} {...rest} />;
    case 'password':
      return (
        <AppPassword
          autoComplete="new-password"
          placeholder={placeholderText}
          {...rest}
        />
      );
    default:
      return null;
  }
};

export default FormControl;
