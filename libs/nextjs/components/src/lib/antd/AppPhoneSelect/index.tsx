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
import type { BaseSelectRef } from '@rc-component/select';
import type { DefaultOptionType, SelectProps } from 'antd/es/select';

const { Option } = Select;

type PhoneSelectValue = {
  region: string;
  numbers: string[];};

type AppPhoneSelectProps = {
  placeholder?: string;
  className?: string;
  style?: CSSProperties;
  disabled?: boolean;
  onChange?: (value: PhoneSelectValue) => void;
  asterisk?: boolean;
  loading?: boolean;
  suffixIcon?: ReactNode;
  mode?: 'tags' | 'multiple';
  children?: ReactNode;
  value?: PhoneSelectValue;
  defaultRegion?: string;
  [key: string]: unknown;};

const AppPhoneSelect: React.FC<AppPhoneSelectProps> = ({
  placeholder,
  className,
  style,
  disabled,
  onChange,
  asterisk,
  loading,
  suffixIcon,
  mode = 'multiple',
  children,
  value,
  defaultRegion = 'IN',
  ...rest
}) => {
  const inputRef = useRef<BaseSelectRef | null>(null);
  const [state, setState] = useState<PhoneSelectValue>({
    region: defaultRegion,
    numbers: [],
  });

  useEffect(() => {
    if (value) {
      setState(value);
    }
  }, [value]);

  const triggerChange = (changed: Partial<PhoneSelectValue>) => {
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
      <StyledSelect
        style={{ width: 80, maxWidth: 80 }}
        variant="borderless"
        styles={{ popup: { root: { margin: 0, padding: 0, minWidth: 200 } } }}
        maxTagCount="responsive"
        value={state.region || 'IN'}
        onChange={handleRegionChange}
        showSearch
        suffixIcon={null}
        disabled={disabled}
        optionFilterProp="children"
        filterOption={filterRegionOption}
        labelRender={(item) => {
          const country = countryCodes.find((c) => c.short === item.value);
          return (
            <span style={{ margin: 0, padding: 0 }}>
              {country?.flag} {country?.code}
            </span>
          );
        }}
      >
        {countryCodes.map((c) => (
          <Option key={c.flag} value={c.short} title={c.code}>
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
          triggerChange({ numbers: val });
        }}
        disabled={disabled}
        {...rest}
      >
        {children}
      </Select>
    </AppFloatingOutline>
  );
};

export default AppPhoneSelect;
