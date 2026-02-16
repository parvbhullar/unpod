import styled from 'styled-components';
import { Form, Input } from 'antd';
import { lighten } from 'polished';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';

const { TextArea } = Input;

export const StyledContentRoot = styled.div`
  //min-width: 630px;
  padding: 12px 0 0 0;

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    min-width: 300px;
  }
`;

export const StyledButton = styled(AppHeaderButton)`
  background-color: ${({ theme }) => theme.palette.success};
  border-color: ${({ theme }) => theme.palette.success};

  &:hover {
    background-color: ${({ theme }) =>
      lighten(0.2, theme.palette.success)} !important;
    border-color: ${({ theme }) =>
      lighten(0.2, theme.palette.success)} !important;
  }
`;

export const StyledFormItem = styled(Form.Item)`
  /* border-bottom: 1px solid #dbdbdb;
  margin-bottom: 12px;*/
`;

export const StyledInput = styled(Input)`
  padding: 4px 0;
`;

export const StyledTextArea = styled(TextArea)`
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
