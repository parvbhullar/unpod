import {ThemeDirection} from '../../constants/AppConst';
import styled from 'styled-components';

export const AppFormControlWrapper = styled.div`
  border: 0;
  margin: 0 0 8px 0;
  display: inline-flex;
  padding: 0;
  position: relative;
  min-width: 0;
  flex-direction: column;
  vertical-align: top;
  width: 100%;

  &.app-date-picker,
  &.app-select {
    width: 100%;
  }
  &.ant-input-wrapper {
    overflow: hidden;
  }

  &.app-number-range-picker {
    margin-bottom: 10px;

    & .app-compact-input {
      display: flex;
      justify-content: space-between;

      & .ant-form-item {
        margin-bottom: 0;
      }

      & .separator {
        color: ${({theme}: { theme: any }) => theme.text.hint};
        display: flex;
        align-items: center;
        justify-content: center;
        width: 5%;
        margin: 0 5px;
      }
    }
  }

  & .input-label.focused,
  &:hover .input-label.shrink {
    color: ${({theme}: { theme: any }) => theme.text.primary};

    .ant-form-item-has-error & {
      color: ${({theme}: { theme: any }) => theme.errorColor};
    }
  }

  &.app-textarea {
    & .input-label {
      top: 0;
      transform: translate(11px, 4px) scale(1);

      &.shrink {
        transform: translate(11px, -6px) scale(0.75);
        top: 0;
      }
    }

    & .ant-input {
      height: auto !important;
    }
  }

  & &.app-number-range-picker {
    & .ant-input-number:hover:first-child {
      border-style: solid;
      border-color: ${({theme}: { theme: any }) =>
  theme.border.color} !important;
      border-right-width: 1px !important;
    }
  }

  &
    .ant-select-focused:not(.ant-select-disabled).ant-select:not(
      .ant-select-customize-input
    )
    .ant-select-selector {
    border-color: transparent !important;
    box-shadow: none;
  }

  &
    .ant-select:not(.ant-select-disabled):not(.ant-select-customize-input)
    .ant-select-selector {
    border-color: transparent !important;
  }

  & .ant-input-number-handler-wrap {
    border-top-right-radius: ${({theme}: { theme: any }) =>
  theme.border.radius};
    border-bottom-right-radius: ${({theme}: { theme: any }) =>
  theme.border.radius};
  }
`;

export const InputLabel = styled.label`
  color: ${({theme}: { theme: any }) => theme.text.placeholder};
  font-size: 16px !important;
  padding: 0;
  display: block;
  transform-origin: ${({theme}: { theme: any }) =>
    theme.direction === ThemeDirection.RTL ? 'top right' : 'top left'};
  top: 50%;
  right: ${({theme}: { theme: any }) =>
    theme.direction === ThemeDirection.RTL ? '22px' : ''};
  left: ${({theme}: { theme: any }) =>
    theme.direction === ThemeDirection.RTL ? '' : '2px'};
  line-height: 1;
  position: absolute;
  pointer-events: none;
  transform: translate(11px, -50%) scale(1);
  transition: color 200ms cubic-bezier(0, 0, 0.2, 1) 0ms,
  all 200ms cubic-bezier(0, 0, 0.2, 1) 0ms;
  z-index: 2;
  text-transform: capitalize;

  &.shrink {
    transform: translate(11px, -6px) scale(0.75);
    top: 0;
  }
`;

export const InputContainer = styled.div`
  color: ${({theme}: { theme: any }) => theme.text.primary};
  cursor: text;
  display: inline-flex;
  position: relative;
  align-items: center;
  border-radius: ${({theme}: { theme: any }) => theme.border.radius};
  height: 100%;
  width: 100%;
  z-index: 1;

  &:focus-open {
    outline: none;
  }

  & .ant-input,
  & .ant-input-textarea,
  & .ant-input-password,
  & .ant-input-search,
  & .ant-input-number-affix-wrapper,
  & .ant-picker,
  & .ant-select,
  & .ant-picker-input,
  & .ant-input-number,
  & .ant-select-selector {
    width: 100%;
    height: 100%;
  }

  & .ant-input,
  & .ant-input-password,
  & .ant-input-search,
  & .ant-input-number-input,
  & .ant-picker,
  & .ant-select,
  & .ant-picker-input {
    height: 40px;

    @media (min-width: ${({theme}: { theme: any }) =>
      theme.breakpoints.xxl}px) {
      height: 40px;
      font-size: ${({theme}: { theme: any }) => theme.font.size.lg};
    }

    @media (min-width: ${({theme}: { theme: any }) =>
      theme.breakpoints.xxl + 320}px) {
      height: 40px;
    }
  }

  & .ant-input,
  & .ant-input-password,
  & .ant-input-search,
  & .ant-picker,
  & .ant-select,
  & .ant-input-number,
  & .ant-input-group-addon,
  & .ant-select-selector {
    border-color: transparent !important;
    box-shadow: none !important;

    &:focus,
    &:hover {
      border-color: transparent !important;
      box-shadow: none !important;
    }
  }

  & .ant-select-single .ant-select-selector .ant-select-selection-item,
  & .ant-select-single .ant-select-selector .ant-select-selection-placeholder {
    line-height: 26px;
    font-size: ${({theme}: { theme: any }) => theme.font.size.lg};
  }

  & .ant-input-affix-wrapper:not(.ant-input-password) {
    padding: 0 11px 0 0;
    margin: 0;
    border: 0 none;

    & > input.ant-input {
      padding: 4px 11px;
      border: 1px solid transparent;
    }
  }

  & .ant-picker-focused,
  & .ant-select-focused,
  & .ant-input-number,
  & .ant-input-affix-wrapper-focused {
    border-color: transparent !important;
    box-shadow: none !important;
  }

  & .app-form-item {
    margin-bottom: 0;
  }

  & .ant-input-number {
    border: 0 none;

    & .ant-input-number-handler-wrap {
      margin-right: 1px;
      height: 98%;
    }
  }

  & .ant-input-group > .ant-input:first-child,
  & .ant-input-group-addon:first-child {
    border-right-width: 1px !important;
    border-right-color: ${({theme}: { theme: any }) =>
      theme.border.color} !important;
  }

  .ant-form-item & .ant-select,
  .ant-form-item & .ant-cascader-picker {
    width: 100%;
  }

  &.focused,
  &:hover {
    & .form-control-fieldset {
      border-color: ${({theme}: { theme: any }) => theme.primaryColor};
    }

    & .ant-input-group > .ant-input:first-child,
    & .ant-input-group-addon:first-child {
      border-right-color: ${({theme}: { theme: any }) =>
        theme.primaryColor} !important;
    }
  }

  .ant-form-item-has-error &,
  .ant-form-item-has-error &.focused,
  .ant-form-item-has-error &:hover {
    & .form-control-fieldset {
      border-color: ${({theme}: { theme: any }) => theme.errorColor};
    }

    & .ant-input-group > .ant-input:first-child,
    & .ant-input-group-addon:first-child {
      border-right-color: ${({theme}: { theme: any }) =>
        theme.errorColor} !important;
    }
  }
`;

export const FormControlFieldset = styled.fieldset`
  top: -6px;
  left: 0;
  right: 0;
  bottom: 0;
  margin: 0;
  border-color: ${({theme}: { theme: any }) => theme.border.color};
  padding: 0 8px;
  overflow: hidden;
  position: absolute;
  border-style: solid;
  border-width: 1px;
  border-radius: inherit;
  pointer-events: none;
  z-index: 1;

  .ant-form-item-has-error & {
    border-color: ${({theme}: { theme: any }) => theme.errorColor};
  }

  & .fieldset-legend {
    width: auto;
    height: 11px;
    display: block;
    padding: 0;
    font-size: 12px;
    max-width: 0.01px;
    text-align: ${({theme}: { theme: any }) => {
      return theme.direction === ThemeDirection.RTL ? 'right' : 'left';
    }};
    transition: max-width 50ms cubic-bezier(0, 0, 0.2, 1) 0ms;
    visibility: hidden;

    &.shrink {
      max-width: 1000px;
      padding: 0 4px 0 4px;
      transition: max-width 100ms cubic-bezier(0, 0, 0.2, 1) 50ms;
    }
  }
`;
