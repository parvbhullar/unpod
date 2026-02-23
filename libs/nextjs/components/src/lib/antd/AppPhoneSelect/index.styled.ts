import styled from 'styled-components';
import {Select} from 'antd';

export const StyledSelect = styled(Select)`
  .ant-select-selector .ant-select-selection-item,
  .ant-select-selector .ant-select-selection-search,
  .ant-select-selection-search {
    padding-right: 0 !important;
  }

  .ant-select-selector {
    padding-right: 0 !important;
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
