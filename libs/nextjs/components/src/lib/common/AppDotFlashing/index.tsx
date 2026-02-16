import React from 'react';
import styled from 'styled-components';
import { Typography } from 'antd';

const { Text } = Typography;

export const StyledDotWrapper = styled(Text)`
  display: inline-flex;
  width: 40px;
  position: relative;
  justify-content: center;
  align-items: center;
  margin-left: 5px;
`;

export const StyledDotFlashing = styled.div`
  position: relative;
  width: 6px;
  height: 6px;
  border-radius: 5px;
  background-color: ${({ theme }) => theme.palette.primary};
  color: ${({ theme }) => theme.palette.primary};
  animation: dot-flashing 1s infinite linear alternate;
  animation-delay: 0.5s;

  &:before,
  &:after {
    content: '';
    display: inline-block;
    position: absolute;
    top: 0;
  }

  &:before {
    left: -10px;
    width: 6px;
    height: 6px;
    border-radius: 5px;
    background-color: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.primary};
    animation: dot-flashing 1s infinite alternate;
    animation-delay: 0s;
  }

  &:after {
    left: 10px;
    width: 6px;
    height: 6px;
    border-radius: 5px;
    background-color: ${({ theme }) => theme.palette.primary};
    color: ${({ theme }) => theme.palette.primary};
    animation: dot-flashing 1s infinite alternate;
    animation-delay: 1s;
  }
`;

type AppDotFlashingProps = {
  [key: string]: any;};

const AppDotFlashing: React.FC<AppDotFlashingProps> = (props) => {
  return (
    <StyledDotWrapper {...props}>
      <StyledDotFlashing />
    </StyledDotWrapper>
  );
};

export default AppDotFlashing;
