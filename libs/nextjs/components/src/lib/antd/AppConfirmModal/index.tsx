import React, {ReactNode} from 'react';
import {Modal} from 'antd';
import {useIntl} from 'react-intl';

type AppConfirmModalProps = {
  open?: boolean;
  title?: string;
  message?: ReactNode;
  onOk?: () => void;
  onCancel?: () => void;
  cancelText?: string;
  okText?: string;
  isDanger?: boolean;
  [key: string]: unknown;
};

const AppConfirmModal: React.FC<AppConfirmModalProps> = ({
                                                           open,
                                                           title = 'alert.title',
                                                           message = 'Are you sure you want to proceed?',
                                                           onOk,
                                                           onCancel,
                                                           cancelText = 'common.cancel',
                                                           okText = 'common.delete',
                                                           isDanger = true,
                                                           ...restProps
                                                         }) => {
  const {formatMessage} = useIntl();

  const onActionConfirm = () => {
    if (onOk) onOk();
  };

  return (
    <Modal
      title={
        formatMessage({id: title}) || formatMessage({id: 'alert.confirm'})
      }
      open={open}
      centered
      width={400}
      destroyOnHidden={true}
      onOk={onActionConfirm}
      onCancel={onCancel}
      okText={formatMessage({id: okText})}
      okButtonProps={{danger: isDanger}}
      cancelText={formatMessage({id: cancelText})}
      {...restProps}
    >
      {message}
    </Modal>
  );
};

export default React.memo(AppConfirmModal);
