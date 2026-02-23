import React, {ReactNode} from 'react';
import clsx from 'clsx';
import {MdCheckCircle} from 'react-icons/md';
import {StyledMenu, StyledMenuItem} from './index.style';

type MenuItemProps = {
  item: AppCustomMenuItem;
  activeKeys?: string[];
  showCheckIcon?: boolean;
  activeCheckIcon?: ReactNode;
};

type AppCustomMenuItem = {
  label: ReactNode;
  icon?: ReactNode;
  rightIcon?: ReactNode;
  key: string;
  onClick?: () => void;
  disabled?: boolean;
};

const MenuItem: React.FC<MenuItemProps> = ({
                                             item,
                                             activeKeys = [],
                                             showCheckIcon = false,
                                             activeCheckIcon,
                                           }) => {
  const {label, icon, rightIcon, key, onClick, disabled} = item;
  return (
    <StyledMenuItem
      onClick={onClick}
      className={clsx('app-custom-menu-item', {
        disabled: disabled,
        active: activeKeys.includes(key),
      })}
      title={label?.toString()}
    >
      {icon}
      <span className="menu-label">{label}</span>

      {showCheckIcon && activeKeys.includes(key) && !disabled && (
        <span className="check-icon">
          {activeCheckIcon || <MdCheckCircle fontSize={18}/>}
        </span>
      )}

      {rightIcon}
    </StyledMenuItem>
  );
};

type AppCustomMenusProps = {
  items: AppCustomMenuItem[];
  activeKeys?: string[];
  showCheckIcon?: boolean;
  activeCheckIcon?: ReactNode;
  [key: string]: any;
};

const AppCustomMenus: React.FC<AppCustomMenusProps> = ({
                                                         items,
                                                         activeKeys,
                                                         showCheckIcon = false,
                                                         activeCheckIcon,
                                                         ...restProps
                                                       }) => {
  return (
    <StyledMenu className={clsx('app-custom-menus')} {...restProps}>
      {items.map((item, index) => (
        <MenuItem
          key={index}
          item={item}
          activeKeys={activeKeys}
          showCheckIcon={showCheckIcon}
          activeCheckIcon={activeCheckIcon}
        />
      ))}
    </StyledMenu>
  );
};

export default AppCustomMenus;
