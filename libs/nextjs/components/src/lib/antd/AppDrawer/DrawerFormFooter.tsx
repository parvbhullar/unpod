import type {ReactNode} from 'react';
import styled from 'styled-components';
import type {FormItemProps} from 'antd';
import {Form, Space} from 'antd';

type StyledFooterProps = {
  $paddingRight?: boolean;
};

export const StyledFooter = styled(Form.Item)<StyledFooterProps>`
  position: sticky;
  bottom: 0;
  z-index: 100;
  background: ${({theme}) => theme.palette.common.white};
  margin: auto 0 !important;
  border-top: 1px solid ${({theme}) => theme.border.color};
  padding-top: 16px !important;
  text-align: right;
  padding-right: ${({$paddingRight}) =>
  $paddingRight ? '24px' : '0'} !important;

  & .ant-btn {
    width: 100px;

    @media (min-width: ${({theme}) => theme.breakpoints.md}px) {
      width: 135px;
    }
  }
`;

export type DrawerFormFooterProps = FormItemProps & {
  children?: ReactNode;
  isTabDrawer?: boolean;
};

export const DrawerFormFooter = ({
                                   children,
                                   isTabDrawer,
                                   ...restProps
                                 }: DrawerFormFooterProps) => {
  return (
    <StyledFooter {...restProps} $paddingRight={isTabDrawer}>
      <Space>{children}</Space>
    </StyledFooter>
  );
};
