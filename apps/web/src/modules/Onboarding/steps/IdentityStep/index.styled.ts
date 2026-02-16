import styled from 'styled-components';
import { Button } from 'antd';

export const StyledInnerContainer = styled.div`
  display: flex;
`;

export const StyledRoot = styled.div`
  scrollbar-width: thin;
  height: calc(100vh - 90px);
  overflow: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    height: calc(100vh - 80px);
  }
`;

export const StyledInputWithButton = styled.div`
  position: relative;
  width: 100%;

  .ant-input {
    padding-right: 110px;
    height: 44px;
  }
`;

export const StyledImportButton = styled(Button)`
  position: absolute;
  right: 6px;
  top: 40%;
  transform: translateY(-50%);
  border-radius: 8px;
  z-index: 99;
`;

export const StyledDivider = styled.div`
  .ant-divider-horizontal.ant-divider-with-text {
    color: ${({ theme }) => theme.palette.text.secondary} !important;
    font-size: 12px !important;
  }
`;
