// components/StyledButton.jsx
import styled, { css, type RuleSet } from 'styled-components';
import React, { ReactNode } from 'react';

type ButtonShape = 'default' | 'round' | 'circle';

const shapeStyles: Record<ButtonShape, RuleSet<object>> = {
  default: css`
    border-radius: 4px;
    padding: 0.5em 1.2em;
  `,
  round: css`
    border-radius: 20px;
    padding: 0.5em 1.5em;
  `,
  circle: css`
    font-size: 18px;
    border-radius: 50%;
    width: 40px !important;
    height: 40px !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  `,
};

type StyledButtonProps = {
  danger?: boolean;
  shape?: ButtonShape;
  color?: string;
};

const StyledButtonWrapper = styled.button.withConfig({
  shouldForwardProp: (prop) =>
    prop !== 'danger' &&
    prop !== 'shape' &&
    prop !== 'color' &&
    prop !== 'variant',
})<StyledButtonProps>`
  background-color: ${({ danger, theme }) =>
    danger ? '#ff4d4f' : theme?.palette?.primary};
  color: ${({ color }) => color || '#fff'};
  border: none;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5em;

  ${({ shape }) => shapeStyles[shape || 'default']};

  &:hover {
    background-color: ${({ danger, theme }) =>
      danger ? '#ff7875' : theme?.palette?.primaryHover};
  }

  &:active {
    background-color: ${({ danger, theme }) =>
      danger ? '#d9363e' : theme?.palette?.primaryActive};
  }
`;

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  icon?: ReactNode;
  shape?: 'default' | 'round' | 'circle';
  danger?: boolean;
  color?: string;
  variant?: string;
};

const Button: React.FC<ButtonProps> = ({ icon, children, ...rest }) => {
  return (
    <StyledButtonWrapper {...rest}>
      {icon && <span>{icon}</span>}
      {children}
    </StyledButtonWrapper>
  );
};
export default Button;
