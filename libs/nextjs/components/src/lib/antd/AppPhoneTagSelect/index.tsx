'use client';
import React, {
  CSSProperties,
  ReactNode,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Select } from 'antd';
import clsx from 'clsx';
import AppFloatingOutline from '../AppFloatingOutline';
import { countryCodes } from '@unpod/constants/CountryData';
import { StyledSelect } from './index.styled';
import { useInfoViewActionsContext } from '@unpod/providers';
import { useIntl } from 'react-intl';
import type { BaseSelectRef } from '@rc-component/select';
import type { DefaultOptionType, SelectProps } from 'antd/es/select';

const { Option } = Select;

type PhoneTagValue = {
  region: string;
  numbers: string[];};

type AppPhoneTagSelectProps = {
  placeholder?: string;
  className?: string;
  style?: CSSProperties;
  disabled?: boolean;
  onChange?: (value: PhoneTagValue) => void;
  asterisk?: boolean;
  loading?: boolean;
  suffixIcon?: ReactNode;
  mode?: 'tags' | 'multiple';
  children?: ReactNode;
  value?: PhoneTagValue;
  defaultRegion?: string;
  maxTags?: number;
  [key: string]: unknown;};

const AppPhoneTagSelect: React.FC<AppPhoneTagSelectProps> = ({
  placeholder,
  className,
  style,
  disabled,
  onChange,
  asterisk,
  loading,
  suffixIcon,
  mode = 'tags',
  children,
  value,
  defaultRegion = '+91',
  maxTags = 10,
  ...rest
}) => {
  const inputRef = useRef<BaseSelectRef | null>(null);
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();
  const [state, setState] = useState<PhoneTagValue>({
    region: defaultRegion,
    numbers: [],
  });

  useEffect(() => {
    if (value) {
      setState(value);
    }
  }, [value]);

  const triggerChange = (changed: Partial<PhoneTagValue>) => {
    const updated = { ...state, ...changed };
    setState(updated);
    onChange?.(updated);
  };

  const handleRegionChange: SelectProps['onChange'] = (val) => {
    triggerChange({
      region: String(val),
    });
  };

  const filterRegionOption: SelectProps<
    string,
    DefaultOptionType
  >['filterOption'] = (input, option) => {
    const inputValue = input.toLowerCase();
    return (
      String(option?.children ?? '')
        .toLowerCase()
        .includes(inputValue) ||
      String(option?.title ?? '')
        .toLowerCase()
        .includes(inputValue) ||
      String(option?.value ?? '')
        .toLowerCase()
        .includes(inputValue)
    );
  };

  return (
    <AppFloatingOutline
      placeholder={placeholder ?? ''}
      addonBefore
      className={clsx('app-phone-select', className)}
      style={style}
      value={state?.numbers && state.numbers.length > 0 ? 'filled' : ''}
      disabled={disabled}
      eleID={inputRef?.current?.nativeElement?.querySelector('input')?.id}
      asterisk={asterisk}
    >
      <React.Fragment>
        <StyledSelect
          style={{ width: 80, maxWidth: 80 }}
          bordered={false}
          dropdownStyle={{ margin: 0, padding: 0, minWidth: 200 }}
          maxTagCount="responsive"
          value={state.region || '+91'}
          onChange={handleRegionChange}
          showSearch
          showArrow={false}
          disabled={disabled}
          optionFilterProp="children"
          filterOption={filterRegionOption}
          labelRender={(item) => {
            const country = countryCodes.find((c) => c.code === item.value);
            return (
              <span style={{ margin: 0, padding: 0 }}>
                {country?.flag} {String(item.value)}
              </span>
            );
          }}
        >
          {countryCodes.map((c) => (
            <Option key={c.flag} value={c.code} title={c.code}>
              {`${c.flag} ${c.code} (${c.name})`}
            </Option>
          ))}
        </StyledSelect>

        <Select
          ref={inputRef}
          style={{ flex: 1 }}
          mode={mode}
          loading={loading}
          maxTagCount="responsive"
          suffixIcon={loading ? undefined : suffixIcon}
          value={state.numbers}
          onChange={(val: string[]) => {
            if (val.length <= maxTags) {
              triggerChange({ numbers: val });
            } else {
              infoViewActionsContext.showError(
                formatMessage(
                  { id: 'advanced.validationMaxTags' },
                  { maxTags: maxTags },
                ),
              );
            }
          }}
          disabled={disabled}
          {...rest}
        >
          {children}
        </Select>
      </React.Fragment>
    </AppFloatingOutline>
  );
};

export default AppPhoneTagSelect;
