import styled from 'styled-components';
import {Select} from 'antd';
import {AppInput} from '../index';

export const StyledAppInput = styled(AppInput as any)`
  .ant-input-group-addon {
    padding: 0 4px !important;
  }

  .ant-input-lg {
    padding: 8px 11px 6px 0 !important;
  }
  .ant-input {
    padding: 8px 11px 6px 0 !important;
  }

  .ant-input-group .ant-input-group-addon {
    padding: 0 4px 0 11px !important;
  }

  .ant-input-group .ant-input-group-addon {
    background: transparent;
    background-color: transparent;
  }
`;
export const StyledSelect = styled(Select)`
  .ant-select-selector {
    padding: 0 !important;
  }
  :where(
      .css-dev-only-do-not-override-l4vdmp
    ).ant-select-single.ant-select-show-arrow
    .ant-select-selection-item,
  :where(
      .css-dev-only-do-not-override-l4vdmp
    ).ant-select-single.ant-select-show-arrow
    .ant-select-selection-search,
  :where(
      .css-dev-only-do-not-override-l4vdmp
    ).ant-select-single.ant-select-show-arrow
    .ant-select-selection-placeholder {
    padding-inline-end: 4px !important;
  }
`;
