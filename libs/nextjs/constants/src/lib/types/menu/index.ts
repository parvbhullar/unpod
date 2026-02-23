import type {ReactNode} from 'react';

export type AppCustomMenuItem = {
  key: string;
  label: ReactNode;
  icon?: ReactNode;
  rightIcon?: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
};
