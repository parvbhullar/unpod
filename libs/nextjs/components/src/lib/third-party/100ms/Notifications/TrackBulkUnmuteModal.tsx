import { useEffect, useState } from 'react';
import {
  HMSNotificationTypes,
  useHMSActions,
  useHMSNotifications,
} from '@100mslive/react-sdk';
import { BsMic } from 'react-icons/bs';
import AppConfirmModal from '../../../antd/AppConfirmModal';

export const TrackBulkUnmuteModal = () => {
  const hmsActions = useHMSActions();
  const [muteNotification, setMuteNotification] = useState(null);
  const notification = useHMSNotifications([
    HMSNotificationTypes.CHANGE_MULTI_TRACK_STATE_REQUEST,
    HMSNotificationTypes.ROOM_ENDED,
    HMSNotificationTypes.REMOVED_FROM_ROOM,
  ]);

  useEffect(() => {
    switch (notification?.type) {
      case HMSNotificationTypes.REMOVED_FROM_ROOM:
      case HMSNotificationTypes.ROOM_ENDED:
        setMuteNotification(null);
        break;
      case HMSNotificationTypes.CHANGE_MULTI_TRACK_STATE_REQUEST:
        if (notification?.data.enabled) {
          setMuteNotification(notification.data);
        }
        break;
      default:
        return;
    }
  }, [notification]);

  console.log('TrackBulkUnmuteModal', notification, muteNotification);
  if (!muteNotification) {
    return null;
  }

  const { requestedBy: peer, tracks, enabled } = muteNotification;
  return (
    <AppConfirmModal
      open={muteNotification}
      title="Track Unmute Request"
      message={`${peer?.name} has requested you to unmute your tracks.`}
      onCancel={(value) => !value && setMuteNotification(null)}
      cancelText={'Accept'}
      okText={'Accept'}
      onOk={() => {
        tracks.forEach((track) => {
          hmsActions.setEnabledTrack(track.id, enabled);
        });
        setMuteNotification(null);
      }}
      isDanger={false}
      icon={<BsMic style={{ fontStyle: 20 }} />}
    />
  );
};
