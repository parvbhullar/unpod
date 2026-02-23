import React, {useEffect, useState} from 'react';
import {HMSNotificationTypes, useHMSNotifications,} from '@100mslive/react-sdk';
import {Modal} from 'antd';

export function PermissionErrorModal() {
  const notification = useHMSNotifications(HMSNotificationTypes.ERROR);
  const [deviceType, setDeviceType] = useState('');
  const [isSystemError, setIsSystemError] = useState(false);
  useEffect(() => {
    if (
      !notification ||
      (notification.data?.code !== 3001 && notification.data?.code !== 3011) ||
      (notification.data?.code === 3001 &&
        notification.data?.message.includes('screen'))
    ) {
      return;
    }
    console.error(`[${notification.type}]`, notification);
    const errorMessage = notification.data?.message;
    const hasAudio = errorMessage.includes('audio');
    const hasVideo = errorMessage.includes('video');
    const hasScreen = errorMessage.includes('screen');
    if (hasAudio && hasVideo) {
      setDeviceType('Camera and Microphone');
    } else if (hasAudio) {
      setDeviceType('Microphone');
    } else if (hasVideo) {
      setDeviceType('Camera');
    } else if (hasScreen) {
      setDeviceType('Screenshare');
    }
    setIsSystemError(notification.data.code === 3011);
  }, [notification]);
  return deviceType ? (
    <Modal
      open
      title={`${deviceType} permissions are blocked`}
      onCancel={(value) => {
        if (!value) {
          setDeviceType('');
        }
      }}
    >
      Access to {deviceType} is required.&nbsp;
      {isSystemError
        ? `Enable permissions for ${deviceType} from sytem settings`
        : `Enable permissions for ${deviceType} from address bar or browser settings`}
    </Modal>
  ) : null;
}
