// @ts-check
import { useCallback } from 'react';
import {
  selectPeerNameByID,
  selectSessionMetadata,
  useHMSActions,
  useHMSStore,
  useHMSVanillaStore
} from '@100mslive/react-sdk';
import { SESSION_STORE_KEY } from '../common/constants';
import { message } from 'antd';

/**
 * set pinned chat message by updating the session store
 */
export const useSetPinnedMessage = () => {
  const hmsActions = useHMSActions();
  const vanillaStore = useHMSVanillaStore();
  const pinnedMessage = useHMSStore(selectSessionMetadata);

  const setPinnedMessage = useCallback(
    /**
     * @param {import('@100mslive/react-sdk').HMSMessage | undefined} messageData
     */
    async (messageData) => {
      const peerName =
        vanillaStore.getState(selectPeerNameByID(messageData?.sender)) ||
        messageData?.senderName;
      const newPinnedMessage = messageData
        ? peerName
          ? `${peerName}: ${messageData.message}`
          : messageData.message
        : null;
      if (newPinnedMessage !== pinnedMessage) {
        await hmsActions.sessionStore
          .set(SESSION_STORE_KEY.PINNED_MESSAGE, newPinnedMessage)
          .catch((err) => message.error(err.description));
      }
    },
    [hmsActions, vanillaStore, pinnedMessage]
  );

  return { setPinnedMessage };
};
