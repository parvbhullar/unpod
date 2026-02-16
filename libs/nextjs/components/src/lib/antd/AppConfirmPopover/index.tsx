'use client';
import React, { ReactNode, useState } from 'react';
import { Button } from 'antd';
import {
  StyledAppConfirmPopover,
  StyledConfirmDeleteActions,
  StyledMessageBody,
} from './index.styled';

type AppConfirmPopoverProps = {
  title?: string;
  message?: string;
  onConfirm?: () => void;
  btnLabels?: [string, string];
  infoMsg?: string;
  children?: ReactNode;
  [key: string]: unknown;};

const AppConfirmPopover: React.FC<AppConfirmPopoverProps> = ({
  title,
  message,
  onConfirm,
  btnLabels = ['Cancel', 'Ok'],
  infoMsg,
  ...restProps
}) => {
  const [openPopover, setOpenPopover] = useState<boolean>(false);
  const handleVisibleChange = (open: boolean) => setOpenPopover(open);

  const onActionConfirm = () => {
    setOpenPopover(false);
    if (onConfirm) onConfirm();
  };

  return (
    <StyledAppConfirmPopover
      overlayClassName="app-confirm-popover"
      content={
        <ConfirmMessage
          infoMsg={infoMsg}
          message={message}
          onConfirm={onActionConfirm}
          onCancel={() => setOpenPopover(false)}
          btnLabels={btnLabels}
        />
      }
      title={title || 'Confirm'}
      trigger="click"
      placement="topRight"
      open={openPopover}
      onOpenChange={handleVisibleChange}
      arrow
      {...restProps}
    />
  );
};

export default React.memo(AppConfirmPopover);

type ConfirmMessageProps = {
  message?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  btnLabels?: [string, string];
  infoMsg?: string;};

export const ConfirmMessage: React.FC<ConfirmMessageProps> = ({
  message = 'Are you sure to perform this onClick?',
  onConfirm,
  onCancel,
  btnLabels = ['Cancel', 'Ok'],
  infoMsg,
}) => {
  const [cancelLabel, confirmLabel] = btnLabels;
  return (
    <React.Fragment>
      {infoMsg && <span>{infoMsg}</span>}
      <StyledMessageBody>{message}</StyledMessageBody>
      <StyledConfirmDeleteActions>
        <Button ghost type="primary" size="small" onClick={onCancel}>
          {cancelLabel}
        </Button>

        <Button type="primary" size="small" onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </StyledConfirmDeleteActions>
    </React.Fragment>
  );
};
