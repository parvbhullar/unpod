import React, { ReactNode } from 'react';
import clsx from 'clsx';
import styled from 'styled-components';

const StyledInputWrapper = styled.div`
  display: inline-flex;
  align-items: center;
  border: ${({ theme }) => theme.border.width}
    ${({ theme }) => theme.border.style} ${({ theme }) => theme.border.color};
  border-radius: ${({ theme }) => theme.radius.base}px;
  font-size: 14px;
  padding: 0 11px;
  height: 40px;

  /*@media screen and (min-width: ${({ theme }) => theme.breakpoints.xxl}px) {
    height: 45px;
    font-size: ${({ theme }) => theme.font.size.lg};
  }

  @media screen and (min-width: ${({ theme }) =>
    theme.breakpoints.md + 320}px) {
    height: 50px;
  }*/

  & .ant-form-item {
    margin-bottom: 0;
  }
`;

type AppInputWrapperProps = {
  className?: string;
  children?: ReactNode;
  [key: string]: unknown;};

const AppInputWrapper: React.FC<AppInputWrapperProps> = ({
  className,
  ...props
}) => {
  return (
    <StyledInputWrapper
      role="input-wrapper"
      aria-label="wrapper"
      className={clsx(className)}
      {...props}
    />
  );
};

export default AppInputWrapper;
