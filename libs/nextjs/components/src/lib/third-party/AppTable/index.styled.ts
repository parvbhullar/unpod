import styled from 'styled-components';
import {Space, Table} from 'antd';
import {rgba} from 'polished';

export const TableResponsive = styled(Table)`
  & .ant-table-cell {
    word-break: break-all;
    white-space: nowrap;
  }

  & .table-row-dark {
    background-color: ${({theme}) =>
  theme.palette.background.default} !important;
  }

  & .ant-table .ant-table-thead > tr > th {
    font-weight: 500;
  }

  .ant-table {
    min-height: 0.01%;
  }

  .ant-table-selection-column {
    padding-left: 20px;
  }

  & .ant-table-bordered > .ant-table-container {
    border-color: ${({theme}) => theme.border.color} !important;

    & > .ant-table-content > table {
      & > thead > tr > th,
      & > tbody > tr > td {
        border-color: ${({theme}) => theme.border.color} !important;
      }
    }

    & .ant-table-cell-row-hover {
      background: ${({theme}) =>
  rgba(theme.palette.primary, 0.15)} !important;
    }
  }

  &.summery {
    & .ant-table .ant-table-thead > tr > th {
      background: ${({theme}) => theme.palette.background.default} !important;
    }

    & .ant-table .ant-table-tbody > tr > td {
      background: ${({theme}) => theme.palette.background.default} !important;

      &:hover {
        background: ${({theme}) =>
  theme.palette.background.default} !important;
      }
    }

    margin-bottom: 20px !important;
  }

  & .ant-table-tbody > tr.ant-table-placeholder {
    color: black;
    letter-spacing: 1px;
  }

  & .ant-checkbox-inner {
    border-radius: 4px !important;
  }
`;

export const StyledTableActions = styled(Space)`
  & .ant-space-item {
    display: inline-flex;
    align-items: center;
  }
`;
