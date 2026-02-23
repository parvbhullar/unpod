'use client';
import React, {Fragment, ReactNode, useState} from 'react';
import {Button} from 'antd';
import {StyledAppDeletePopoverWrapper, StyledConfirmDeleteActions, StyledMessageBody,} from './index.styled';
import {useIntl} from 'react-intl';

type AppConfirmDeletePopoverProps = {
  title?: string;
  message?: string;
  okBtnText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  children?: ReactNode;
  [key: string]: unknown;
};

const AppConfirmDeletePopover: React.FC<AppConfirmDeletePopoverProps> = ({
                                                                           title,
                                                                           message,
                                                                           okBtnText,
                                                                           onConfirm,
                                                                           onCancel,
                                                                           ...restProps
                                                                         }) => {
  const [openPopover, setOpenPopover] = useState<boolean>(false);
  const handleVisibleChange = (open: boolean) => setOpenPopover(open);

  const onDeleteConfirm = () => {
    setOpenPopover(false);
    if (onConfirm) onConfirm();
  };

  return (
    <StyledAppDeletePopoverWrapper
      content={
        <DeleteMessage
          message={message}
          okBtnText={okBtnText}
          onConfirm={onDeleteConfirm}
          onCancel={() => {
            setOpenPopover(false);
            if (onCancel) onCancel();
          }}
        />
      }
      title={title || 'Delete Record'}
      trigger="click"
      placement="left"
      open={openPopover}
      onOpenChange={handleVisibleChange}
      {...restProps}
    />
  );
};

export default AppConfirmDeletePopover;

type DeleteMessageProps = {
  message?: string;
  okBtnText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
};

export const DeleteMessage: React.FC<DeleteMessageProps> = ({
                                                              message = 'Are you sure to delete this record?',
                                                              okBtnText = 'Delete',
                                                              onConfirm,
                                                              onCancel,
                                                            }) => {
  const {formatMessage} = useIntl();
  return (
    <Fragment>
      <StyledMessageBody>{message}</StyledMessageBody>
      <StyledConfirmDeleteActions>
        <Button
          ghost
          type="primary"
          size="small"
          shape="round"
          onClick={onCancel}
        >
          {formatMessage({id: 'common.cancel'})}
        </Button>
        <Button
          type="primary"
          size="small"
          shape="round"
          onClick={onConfirm}
          danger
        >
          {okBtnText || formatMessage({id: 'common.delete'})}
        </Button>
      </StyledConfirmDeleteActions>
    </Fragment>
  );
};
