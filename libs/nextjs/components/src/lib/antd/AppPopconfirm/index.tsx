import React, { ReactNode } from 'react';
import { Popconfirm } from 'antd';

type AppPopconfirmProps = {
  title?: string;
  description?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  children?: ReactNode;
  [key: string]: unknown;};

const AppPopconfirm: React.FC<AppPopconfirmProps> = ({
  title = 'Delete Record',
  description = 'Are you sure to delete this record?',
  ...props
}) => {
  return (
    <Popconfirm
      icon={null}
      okText="Confirm"
      cancelText="Cancel"
      cancelButtonProps={{ shape: 'round' }}
      okButtonProps={{ danger: true, shape: 'round' }}
      placement="left"
      title={title}
      description={description}
      {...props}
    />
  );
};

export default AppPopconfirm;
