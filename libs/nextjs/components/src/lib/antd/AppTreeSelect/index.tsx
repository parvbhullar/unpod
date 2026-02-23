'use client';
import React, {CSSProperties, ReactNode, useEffect, useMemo, useRef, useState,} from 'react';
import AppFloatingOutline from '../AppFloatingOutline';
import {TreeSelect} from 'antd';
import clsx from 'clsx';
import type {BaseSelectRef} from '@rc-component/select';
import type {TreeSelectProps} from 'antd/es/tree-select';

type AppTreeSelectProps = {
  placeholder?: string;
  children?: ReactNode;
  defaultValue?: string | number | object | unknown[] | null;
  value?: string | number | object | unknown[] | null;
  className?: string;
  style?: CSSProperties;
  disabled?: boolean;
  onChange?: (value: string | number | object | unknown[] | null) => void;
  asterisk?: boolean;
  id?: string;
  [key: string]: unknown;
};

const AppTreeSelect: React.FC<AppTreeSelectProps> = ({
                                                       placeholder,
                                                       children,
                                                       defaultValue,
                                                       value,
                                                       className = '',
                                                       style,
                                                       disabled = false,
                                                       onChange,
                                                       asterisk,
                                                       ...restProps
                                                     }) => {
  const [inputVal, setInputVal] = useState<
    string | number | object | unknown[] | null
  >(value ?? defaultValue ?? null);
  const inputRef = useRef<BaseSelectRef | null>(null);
  const inputId = useMemo(() => {
    if (restProps?.id) return String(restProps.id);
    return (
      inputRef.current?.nativeElement
        ?.querySelector('input')
        ?.getAttribute('id') || ''
    );
  }, [restProps?.id]);

  useEffect(() => {
    setInputVal(value ?? defaultValue ?? null);
  }, [value, defaultValue]);

  const onSelectChange: TreeSelectProps['onChange'] = (val) => {
    setInputVal(val);
    if (onChange) onChange(val as string | number | object | unknown[] | null);
  };

  return (
    <AppFloatingOutline
      placeholder={typeof placeholder === 'string' ? placeholder : ''}
      className={clsx('app-select', className)}
      style={style}
      value={inputVal}
      disabled={disabled}
      eleID={inputId}
      asterisk={asterisk}
    >
      <TreeSelect
        showSearch
        treeNodeFilterProp="title"
        placeholder=""
        maxTagCount="responsive"
        onChange={onSelectChange}
        defaultValue={defaultValue}
        value={inputVal}
        disabled={disabled}
        {...restProps}
        ref={inputRef}
      >
        {children}
      </TreeSelect>
    </AppFloatingOutline>
  );
};

export default React.memo(AppTreeSelect);
