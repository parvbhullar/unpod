import styled from 'styled-components';
import { Input } from 'antd';

export const StyledInput = styled(Input)`
  border-radius: 12px;

  .ant-input-search-button svg {
    font-size: 20px;
  }
  .ant-input-search-button:hover {
    background: none !important;
  }
`;
