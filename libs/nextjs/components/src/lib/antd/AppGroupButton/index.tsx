import React from 'react';
import type { ButtonProps } from 'antd';
import { Button } from 'antd';
import { StyledButtonWrapper } from './index.styled';

type ButtonOption = {
  id: string | number;
  label: React.ReactNode;
  [key: string]: unknown;};

type AppGroupButtonProps = {
  activeId?: ButtonOption['id'];
  onChange: (id: ButtonOption['id'], option: ButtonOption) => void;
  options: ButtonOption[];
  size?: ButtonProps['size'];};

const AppGroupButton: React.FC<AppGroupButtonProps> = ({
  activeId,
  onChange,
  options,
  size = 'middle',
}) => {
  const onButtonClick = (id: string | number, option: ButtonOption) => {
    if (onChange) onChange(id, option);
  };
  return (
    <StyledButtonWrapper className="group-button">
      {options?.map((option, index) => (
        <Button
          key={index}
          type="primary"
          size={size}
          ghost={option.id !== activeId}
          onClick={() => onButtonClick(option.id, option)}
        >
          {option.label}
        </Button>
      ))}
    </StyledButtonWrapper>
  );
};

export default React.memo(AppGroupButton);
