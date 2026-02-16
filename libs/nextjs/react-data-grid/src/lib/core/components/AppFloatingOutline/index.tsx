import React, { ReactNode, useEffect, useRef, useState } from 'react';
import {
  AppFormControlWrapper,
  FormControlFieldset,
  InputContainer,
  InputLabel,
} from './index.styled';
import { useAutoComplete } from '../../hooks/useAutoComplete';

type Props = {
  placeholder: string;
  children: ReactNode;
  className?: string;
  value?: any;
  disabled?: boolean;
  asterisk?: boolean;
  [key: string]: any;
};

const AppFloatingOutline = ({
  placeholder,
  value,
  disabled,
  className,
  children = false,
  asterisk = false,
  ...restProps
}: Props) => {
  const [isFocused, setFocused] = useState<boolean>(false);
  const { filled, setFilled } = useAutoComplete();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setFilled(false);
  }, [isFocused]);

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
  const shrinkClass = (isFocused && !disabled) || canShrink() ? 'shrink' : '';

  return (
    <AppFormControlWrapper
      ref={wrapperRef}
      className={`${className} ${focusedClass}`}
      onFocus={() => setFocused(true)}
      onKeyDown={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      role="float-container"
      {...restProps}
    >
      <InputLabel
        className={`input-label ${shrinkClass} ${focusedClass}`}
        role="label-placeholder"
      >
        {placeholder}{' '}
        {asterisk && (
          <span aria-label="asterisk" role="asterisk">
            *
          </span>
        )}
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

/*AppFloatingOutline.defaultProps = {
  disabled: false,
  asterisk: false,
};*/

export default React.memo(AppFloatingOutline);
