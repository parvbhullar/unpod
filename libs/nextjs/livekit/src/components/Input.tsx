// components/StyledInput.jsx
import styled, {css, type RuleSet} from 'styled-components';

type InputSize = 'small' | 'default' | 'large';
type InputStatus = 'error' | 'warning' | 'success';

// Optional size styles
const sizeStyles: Record<InputSize, RuleSet<object>> = {
  small: css`
    padding: 4px 8px;
    font-size: 12px;
  `,
  default: css`
    padding: 6px 12px;
    font-size: 14px;
  `,
  large: css`
    padding: 8px 14px;
    font-size: 16px;
  `,
};

// Optional status styles (like AntD)
const statusStyles: Partial<Record<InputStatus, RuleSet<object>>> = {
  error: css`
    border-color: #ff4d4f;

    &:focus {
      box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.2);
    }
  `,
  warning: css`
    border-color: #faad14;

    &:focus {
      box-shadow: 0 0 0 2px rgba(250, 173, 20, 0.2);
    }
  `,
  success: css`
    border-color: #52c41a;

    &:focus {
      box-shadow: 0 0 0 2px rgba(82, 196, 26, 0.2);
    }
  `,
};

type StyledInputProps = {
  size?: InputSize;
  status?: InputStatus;
  fullWidth?: boolean;
};

const Input = styled.input.withConfig({
  shouldForwardProp: (prop) =>
    prop !== 'size' && prop !== 'status' && prop !== 'fullWidth',
})<StyledInputProps>`
  width: 100%;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  outline: none;
  transition: all 0.2s ease-in-out;
  ${({size}) => sizeStyles[size || 'default']};
  ${({status}) => (status ? statusStyles[status] : undefined)};

  &:focus {
    border-color: ${({theme}) => theme?.palette?.primaryActive};
    //box-shadow: 0 0 0 1px rgba(22, 119, 255, 0.2);
  }

  &::placeholder {
    color: #bfbfbf;
  }

  ${({fullWidth}) =>
    fullWidth &&
    css`
      width: 100%;
    `}
`;

export default Input;
