'use client';
import React, {ReactNode, useEffect, useRef, useState} from 'react';
import {AppFormControlWrapper, FormControlFieldset, InputContainer, InputLabel,} from './index.styled';
import {useAutoComplete} from '@unpod/custom-hooks';

type AppFloatingOutlineProps = {
  placeholder: string | undefined;
  value?: string | number | unknown[] | object | null;
  eleID?: string;
  disabled?: boolean | string | number;
  className?: string;
  children: ReactNode;
  asterisk?: boolean;
  addonBefore?: boolean | ReactNode;
  [key: string]: unknown;
};

const AppFloatingOutline: React.FC<AppFloatingOutlineProps> = ({
                                                                 placeholder,
                                                                 value = '',
                                                                 eleID = '',
                                                                 disabled = false,
                                                                 className = '',
                                                                 children,
                                                                 asterisk = false,
                                                                 addonBefore = false,
                                                                 ...restProps
                                                               }) => {
  const [isFocused, setFocused] = useState<boolean>(false);
  const {filled, setFilled} = useAutoComplete();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFilled(false);
  }, [isFocused, setFilled]);

  useEffect(() => {
    if (value && Array.isArray(value) && !value.length) {
      setFocused(false);
    }
  }, [value]);

  const canShrink = () => {
    if (typeof value === 'number' && value >= 0) {
      return true;
    } else if (Array.isArray(value)) {
      return !!value.length;
    } else if (value) {
      return true;
    } else if (filled) {
      return true;
    }
    return false;
  };

  const focusedClass = isFocused && !disabled ? 'focused' : '';
  const addonBeforeClass = addonBefore ? 'addon-before' : '';
  const shrinkClass = (isFocused && !disabled) || canShrink() ? 'shrink' : '';

  return (
    <AppFormControlWrapper
      ref={wrapperRef}
      className={`${className} ${focusedClass}`}
      onFocus={() => setFocused(true)}
      onKeyDown={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    >
      <InputLabel
        className={`input-label ${shrinkClass} ${focusedClass} ${addonBeforeClass}`}
        htmlFor={eleID}
      >
        {placeholder} {asterisk && <span aria-label="asterisk">*</span>}
      </InputLabel>
      <InputContainer className={`${focusedClass}`}>
        {children}

        <FormControlFieldset
          className="form-control-fieldset"
          aria-hidden="true"
        >
          <legend className={`fieldset-legend ${shrinkClass}`}>
            <span>
              {placeholder} {asterisk && <span>*</span>}
            </span>
          </legend>
        </FormControlFieldset>
      </InputContainer>
    </AppFormControlWrapper>
  );
};

export default React.memo(AppFloatingOutline);
