import { useState } from 'react';
import type { PopoverProps } from 'antd';
import { Popconfirm } from 'antd';
import type { ConfirmWindowProps } from '../../models/data-grid';

const ConfirmWindow = ({
  title,
  message = 'Are you sure to delete this record?',
  onConfirm,
  onCancel,
  canBtnText = 'Cancel',
  confBtnText = 'Yes',
  ...restProps
}: PopoverProps & ConfirmWindowProps) => {
  const [open, setOpen] = useState(false);
  const handleVisibleChange = (open: boolean) => setOpen(open);

  const onConfirmClick = () => {
    setOpen(false);
    if (onConfirm) onConfirm();
  };

  return (
    <Popconfirm
      icon={null}
      title={title || 'Delete Row'}
      description={message}
      onConfirm={onConfirmClick}
      okText={confBtnText}
      cancelText={canBtnText}
      onCancel={() => {
        setOpen(false);
        if (onCancel) onCancel();
      }}
      trigger="click"
      placement="left"
      open={open}
      onOpenChange={handleVisibleChange}
      {...restProps}
    />
  );
};

export default ConfirmWindow;
