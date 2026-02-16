import { useEffect, useState } from 'react';
import {
  HMSNotificationTypes,
  useHMSNotifications,
} from '@100mslive/react-sdk';
import { ToastManager } from '../Toast/ToastManager';
import { ToastConfig } from '../Toast/ToastConfig';
import { Modal, Spin } from 'antd';

const notificationTypes = [
  HMSNotificationTypes.RECONNECTED,
  HMSNotificationTypes.RECONNECTING,
  HMSNotificationTypes.ERROR,
];
const isQA = process.env.REACT_APP_ENV === 'qa';
let notificationId = null;
export const ReconnectNotifications = () => {
  const notification = useHMSNotifications(notificationTypes);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (
      notification?.type === HMSNotificationTypes.ERROR &&
      notification?.data?.isTerminal
    ) {
      console.log('Error ', notification.data?.description);
      setOpen(false);
    } else if (notification?.type === HMSNotificationTypes.RECONNECTED) {
      console.log('Reconnected');
      notificationId = ToastManager.replaceToast(
        notificationId,
        ToastConfig.RECONNECTED.single()
      );
      setOpen(false);
    } else if (notification?.type === HMSNotificationTypes.RECONNECTING) {
      console.log('Reconnecting');
      if (isQA) {
        ToastManager.removeToast(notificationId);
        setOpen(true);
      } else {
        notificationId = ToastManager.replaceToast(
          notificationId,
          ToastConfig.RECONNECTING.single(notification.data.message)
        );
      }
    }
  }, [notification]);
  if (!open || !isQA) return null;
  return (
    <Modal open={open}>
      <div
        style={{
          width: 'fit-content',
          maxWidth: '80%',
          padding: '12px 24px',
          position: 'relative',
          top: 'unset',
          bottom: 10,
          transform: 'translate(-50%, -100%)',
          animation: 'none !important',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'inline', margin: '0.25rem' }}>
            <Spin size="large" />
          </div>
          <div css={{ fontSize: 14 }}>
            You lost your network connection. Trying to reconnect.
          </div>
        </div>
      </div>
    </Modal>
  );
};
