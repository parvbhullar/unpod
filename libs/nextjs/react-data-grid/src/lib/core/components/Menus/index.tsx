import clsx from 'clsx';
import { StyledMenu, StyledMenuItem } from './index.style';
import { MenuItemProps } from '../../models/data-grid';
import ConfirmWindow from '../ConfirmWindow';

const MenuItem = ({
  label,
  icon,
  onClick,
  confirmWindowProps,
  disabled,
}: MenuItemProps) => {
  return confirmWindowProps ? (
    <ConfirmWindow {...confirmWindowProps}>
      <StyledMenuItem className={clsx({ disabled: disabled })}>
        {icon}
        <span>{label}</span>
      </StyledMenuItem>
    </ConfirmWindow>
  ) : (
    <StyledMenuItem onClick={onClick} className={clsx({ disabled: disabled })}>
      {icon}
      <span>{label}</span>
    </StyledMenuItem>
  );
};

const Menus = ({ items }: { items: MenuItemProps[] }) => {
  return (
    <StyledMenu>
      {items.map((item, index) => (
        <MenuItem key={index} {...item} />
      ))}
    </StyledMenu>
  );
};

export default Menus;
