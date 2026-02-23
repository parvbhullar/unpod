import {Select} from 'antd';
import {StyledAppInput, StyledSelect} from './index.styled';
import {countryCodes} from '@unpod/constants/CountryData';
import {useIntl} from 'react-intl';
import type {DefaultOptionType} from 'antd/es/select';
import type {ChangeEvent} from 'react';

const {Option} = Select;

type PhoneValue = {
  countryCode: string;
  number?: string;
};

type AppPhoneInputProps = {
  value?: PhoneValue;
  onChange?: (value: PhoneValue) => void;
};

const AppPhoneInput: React.FC<AppPhoneInputProps> = ({
                                                       value = {countryCode: '+91'},
                                                       onChange,
                                                     }) => {
  const {formatMessage} = useIntl();
  const triggerChange = (changedValue: Partial<PhoneValue>) => {
    onChange?.({
      ...value,
      ...changedValue,
    });
  };

  return (
    <StyledAppInput
      addonBefore={
        <StyledSelect
          showSearch
          showArrow={false}
          value={value?.countryCode || '+91'}
          bordered={false}
          onChange={(val) => triggerChange({countryCode: String(val)})}
          style={{margin: 0, padding: 0}}
          dropdownStyle={{margin: 0, padding: 0, minWidth: 200}}
          optionFilterProp="children"
          filterOption={(input, option) => {
            const opt = option as DefaultOptionType | undefined;
            const inputValue = input.toLowerCase();
            return (
              String(opt?.key ?? '')
                .toLowerCase()
                .includes(inputValue) ||
              String(opt?.title ?? '')
                .toLowerCase()
                .includes(inputValue) ||
              String(opt?.value ?? '')
                .toLowerCase()
                .includes(inputValue)
            );
          }}
          labelRender={(c) => {
            const country = countryCodes.find((cc) => cc.code === c.value);
            return (
              <span style={{margin: 0, padding: 0}}>
                {country?.flag} {String(c.value)}
              </span>
            );
          }}
        >
          {countryCodes.map((c) => (
            <Option key={c.flag} value={c.code} title={c.name}>
              <span style={{margin: 0, padding: 0}}>
                {`${c.flag} ${c.code} (${c.name})`}
              </span>
            </Option>
          ))}
        </StyledSelect>
      }
      placeholder={formatMessage({id: 'form.phoneNumber'})}
      value={value?.number}
      onChange={(e: ChangeEvent<HTMLInputElement>) =>
        triggerChange({number: e.target.value})
      }
      maxLength={11}
      style={{flex: 1}}
    />
  );
};

export default AppPhoneInput;
