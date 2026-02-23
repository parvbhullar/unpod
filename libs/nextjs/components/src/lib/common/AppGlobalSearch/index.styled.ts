import styled from 'styled-components';
import {Input} from 'antd';

export const StyledSearch = styled(Input.Search)`
  display: flex;
  min-width: 0;
  align-items: center;
  border: solid 1px #c3c3c3;
  border-radius: 24px;
  overflow: hidden;
  width: 320px;
  height: 40px;

  & .ant-input-wrapper {
    display: flex;
    min-width: 0;
    flex-direction: row-reverse;

    .ant-input-affix-wrapper {
      border-start-start-radius: 0 !important;
      border-end-start-radius: 0 !important;
      border-right: 0 none;

      &:hover,
      &:focus {
        border-color: #c3c3c3;
        box-shadow: none;
      }
    }

    .ant-input {
      border: 0 none;
      &:focus {
        box-shadow: none;
      }
    }

    .ant-input-search-button {
      border: 0 none;
      box-shadow: none;
    }

    .ant-input-group-addon {
      //margin: -2px 0 0 0;
      //inset-inline-start: 0 !important;
      width: auto;

      & button {
        border-start-end-radius: 0 !important;
        border-end-end-radius: 0 !important;
      }
    }
  }
`;
