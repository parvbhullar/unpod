import React from 'react';
import {BsChatText, BsPerson} from 'react-icons/bs';
import {MdSignalWifiStatusbarConnectedNoInternet} from 'react-icons/md';
import {ImConnection} from 'react-icons/im';
import {TbHandStop} from 'react-icons/tb';

// const isChatOpen = () => {
//   return (
//     hmsStore.getState(selectAppData(APP_DATA.sidePane)) ===
//     SIDE_PANE_OPTIONS.CHAT
//   );
// };
//
// const ChatAction = ({_, ref}) => {
//   return (
//     <Button
//       outlined
//       as="div"
//       variant="standard"
//       css={{ w: 'max-content' }}
//       onClick={() => {
//         hmsActions.setAppData(APP_DATA.sidePane, SIDE_PANE_OPTIONS.CHAT);
//       }}
//       ref={ref}
//     >
//       Open Chat
//     </Button>
//   );
// };

export const ToastConfig = {
  PEER_LIST: {
    single: function (notification) {
      if (notification.data.length === 1) {
        return {
          title: `${notification.data[0]?.name} joined`,
          icon: <BsPerson fontSize={20}/>,
        };
        // return message.info(`${notification.data[0]?.name} joined`);
      }
      return {
        title: `${notification.data[notification.data.length - 1]?.name} and ${
          notification.data.length - 1
        } others joined`,
        icon: <BsPerson fontSize={20}/>,
      };
      // return message.info(
      //   `${notification.data[notification.data.length - 1]?.name} and and ${
      //     notification.data.length - 1
      //   } others joined`
      // );
    },
    multiple: (notifications) => {
      return {
        title: `${notifications[0].data.name} and ${
          notifications.length - 1
        } others joined`,
        icon: <BsPerson fontSize={20}/>,
      };
      // return message.info(
      //   `${notifications[0].data.name} and ${
      //     notifications.length - 1
      //   } others joined`
      // );
    },
  },
  PEER_JOINED: {
    single: function (notification) {
      return {
        title: `${notification.data?.name} joined`,
        icon: <BsPerson fontSize={20}/>,
      };
      // return message.info(`${notification.data?.name} joined`);
    },
    multiple: function (notifications) {
      return {
        title: `${notifications[notifications.length - 1].data.name} and ${
          notifications.length - 1
        } others joined`,
        icon: <BsPerson fontSize={20}/>,
      };
      // return message.info(
      //   `${notifications[notifications.length - 1].data.name} and ${
      //     notifications.length - 1
      //   } others joined`
      // );
    },
  },
  PEER_LEFT: {
    single: function (notification) {
      return {
        title: `${notification.data?.name} left`,
        icon: <BsPerson fontSize={20}/>,
      };
      // return message.info(`${notification.data?.name} left`);
    },
    multiple: function (notifications) {
      return {
        title: `${notifications[notifications.length - 1].data.name} and ${
          notifications.length - 1
        } others left`,
        icon: <BsPerson fontSize={20}/>,
      };

      // return message.info(
      //   `${notifications[notifications.length - 1].data.name} and ${
      //     notifications.length - 1
      //   } others left`
      // );
    },
  },
  METADATA_UPDATED: {
    single: (notification) => {
      return {
        title: `${notification.data?.name} raised hand`,
        icon: <TbHandStop fontSize={20}/>,
      };
      // return message.info(`${notification.data?.name} raised hand`);
    },
    multiple: (notifications) => {
      return {
        title: `${notifications[notifications.length - 1].data?.name} and ${
          notifications.length - 1
        } others raised hand`,
        icon: <TbHandStop fontSize={20}/>,
      };
      // return message.info(
      //   `${notifications[notifications.length - 1].data?.name} and ${
      //     notifications.length - 1
      //   } others raised hand`
      // );
    },
  },
  NEW_MESSAGE: {
    single: (notification) => {
      return {
        title: `New message from ${notification.data?.senderName}`,
        icon: <BsChatText fontSize={20}/>,
        // action: isChatOpen() ? null : <ChatAction />,
      };
      // return message.info(`New message from ${notification.data?.senderName}`);
    },
    multiple: (notifications) => {
      return {
        title: `${notifications.length} new messages`,
        icon: <BsChatText fontSize={20}/>,
        // action: isChatOpen() ? null : <ChatAction />,
      };
      // return message.info(`${notifications.length} new messages`);
    },
  },
  RECONNECTED: {
    single: () => {
      return {
        title: `You are now connected`,
        icon: <ImConnection fontSize={20}/>,
        variant: 'success',
        duration: 3000,
      };
      // return message.success(`You are now connected`);
    },
  },
  RECONNECTING: {
    single: (message) => {
      return {
        title: `You are offline for now. while we try to reconnect, please check
        your internet connection. ${message}.
      `,
        icon: <MdSignalWifiStatusbarConnectedNoInternet fontSize={20}/>,
        variant: 'warning',
        duration: 30000,
      };
      // return message.warning(`You are offline for now. while we try to reconnect, please check
      //   your internet connection. ${message}.
      // `);
    },
  },
};
