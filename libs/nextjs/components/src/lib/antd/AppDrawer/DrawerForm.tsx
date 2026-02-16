import styled from 'styled-components';
import type { FormProps } from 'antd';
import { Form } from 'antd';

type DrawerFormProps = Omit<FormProps, 'children'> & {
  children?: React.ReactNode;
};

export const StyledForm = styled(Form)<DrawerFormProps>`
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;

  & .ant-form-item {
    //margin-bottom: 10px;
  }
`;

export const DrawerForm = (props: DrawerFormProps) => {
  return <StyledForm {...props} />;
};
