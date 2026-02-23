'use client';
import React, {CSSProperties, useEffect, useMemo, useRef, useState,} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import {DatePicker} from 'antd';
import {Dayjs} from 'dayjs';
import type {RangePickerProps} from 'antd/es/date-picker';
import type {RangePickerRef} from '@rc-component/picker/es/interface';

type AppRangePickerProps = {
  placeholder?: string | [string, string, string];
  className?: string;
  style?: CSSProperties;
  defaultValue?: RangePickerProps['defaultValue'];
  value?: RangePickerProps['value'];
  disabled?: boolean;
  onChange?: (
    dates: [Dayjs | null, Dayjs | null] | null,
    dateStrings: [string, string],
  ) => void;
  asterisk?: boolean;
  format?: string;
  id?: string;
  [key: string]: unknown;
};

const AppRangePicker: React.FC<AppRangePickerProps> = ({
                                                         placeholder = ['Date', 'Start', 'End'],
                                                         className = '',
                                                         style,
                                                         defaultValue,
                                                         value,
                                                         disabled = false,
                                                         onChange,
                                                         asterisk,
                                                         format,
                                                         ...restProps
                                                       }) => {
  const [inputVal, setInputVal] = useState<
    string | [string, string] | undefined
  >(undefined);
  const [pickerPlaceholder, setPickerPlaceholder] = useState<string[]>(
    typeof placeholder === 'string' ? [placeholder] : placeholder,
  );

  const inputRef = useRef<RangePickerRef | null>(null);
  const inputId = useMemo(() => {
    if (restProps?.id) return String(restProps.id);
    return (
      inputRef.current?.nativeElement
        ?.querySelector('input')
        ?.getAttribute('id') || ''
    );
  }, [restProps?.id]);

  useEffect(() => {
    setPickerPlaceholder(
      typeof placeholder === 'string' ? [placeholder] : placeholder,
    );
  }, [placeholder]);

  useEffect(() => {
    if (value || defaultValue) {
      setInputVal('filled');
    }
  }, [value, defaultValue]);

  const onDatePickerChange: RangePickerProps['onChange'] = (
    dates,
    dateStrings,
  ) => {
    setInputVal(dateStrings);
    if (onChange)
      onChange(dates as [Dayjs | null, Dayjs | null] | null, dateStrings);
  };

  const [placeholder1, placeholder2, placeholder3] = pickerPlaceholder;

  return (
    <AppFloatingOutline
      placeholder={placeholder1}
      className={`app-date ${className}`}
      style={style}
      value={inputVal || placeholder2}
      disabled={disabled}
      eleID={inputId}
      asterisk={asterisk}
    >
      <DatePicker.RangePicker
        placeholder={[placeholder2 || '', placeholder3 || '']}
        value={value}
        format={format ? format : 'DD-MM-YYYY'}
        autoComplete="off"
        disabled={disabled}
        defaultValue={defaultValue}
        onChange={onDatePickerChange}
        {...restProps}
        ref={inputRef}
      />
    </AppFloatingOutline>
  );
};

export default React.memo(AppRangePicker);
