import styled from 'styled-components';
import {Input} from 'antd';
import {AppHeaderButton} from '../../common/AppPageHeader';
import {GlobalTheme} from '@unpod/constants';

const {TextArea} = Input;

export const StyledContentRoot = styled.div`
  min-width: 500px;

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    min-width: 100%;
  }

  .ant-form-item-with-help .ant-form-item-explain {
    position: absolute;
  }
`;

export const StyledCallButton = styled(AppHeaderButton)`
  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    height: 40px !important;
    border-radius: ${({theme}: { theme: GlobalTheme }) =>
  theme.radius.base + 20}px !important;
  }
`;

export const StyledEditButton = styled(AppHeaderButton)`
  width: 100px;

  @media (max-width: ${({theme}: { theme: GlobalTheme }) =>
  theme.breakpoints.sm}px) {
    height: 40px !important;
    border-radius: ${({theme}: { theme: GlobalTheme }) =>
  theme.radius.base + 20}px !important;
  }
`;

export const StyledInput = styled(TextArea)`
  padding: 4px 0;
  resize: none;
`;

export const StyledBottomBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
`;
