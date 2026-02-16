import { useState } from 'react';
import {
  selectIsConnectedToRoom,
  selectPeerCount,
  selectPermissions,
  useHMSActions,
  useHMSStore,
} from '@100mslive/react-sdk';
import { isStreamingKit } from '../../common/utils';
import { useParams, useRouter } from 'next/navigation';
import { IoMdAlert } from 'react-icons/io';
import { ImPhoneHangUp } from 'react-icons/im';
import { Button, Checkbox, Dropdown, Modal, Space, Tooltip } from 'antd';
import { MdCallEnd, MdExitToApp } from 'react-icons/md';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { useStreamContext } from '../../StreamContextProvider';
import { useOrgActionContext } from '@unpod/providers';
import { isHostUser } from '@unpod/helpers/StreamHelper';

export const LeaveRoom = () => {
  const router = useRouter();
  const { orgSlug, spaceSlug, postSlug } = useParams();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { setCallRecording } = useOrgActionContext();
  const { post } = useStreamContext();

  const [showEndRoomModal, setShowEndRoomModal] = useState(false);
  const [lockRoom, setLockRoom] = useState(false);
  const isConnected = useHMSStore(selectIsConnectedToRoom);
  const permissions = useHMSStore(selectPermissions);
  const hmsActions = useHMSActions();
  const peerCount = useHMSStore(selectPeerCount);
  const isStreamKit = isStreamingKit();

  const redirectToLeavePage = () => {
    router.push(`/${orgSlug}/${spaceSlug}/${postSlug}`);
    // if (params.role) {
    //   navigate("/leave/" + params.roomId + "/" + params.role);
    // } else {
    //   navigate("/leave/" + params.roomId);
    // }
  };

  const leaveRoom = () => {
    hmsActions.leave();
    router.push(`/${orgSlug}/${spaceSlug}/`);
  };

  const endRoom = () => {
    getDataApi(`threads/${post.slug}/livesession/stop/`, infoViewActionsContext)
      .then(() => {
        setCallRecording(false);
        hmsActions.endRoom(lockRoom, 'End Room');
        redirectToLeavePage();
      })
      .catch((err) => {
        console.log(err);
      });
  };

  const items = [
    {
      label: (
        <Space gap={4}>
          <IoMdAlert fontSize={20} />
          <div>End Call for All</div>
        </Space>
      ),
      key: 'end-all',
    },
    {
      label: (
        <Space gap={4}>
          <MdExitToApp fontSize={20} />
          <div>Leave {isStreamKit ? 'Studio' : 'Call'}</div>
        </Space>
      ),
      key: 'exit',
    },
  ];

  const onMenuClick = ({ key }) => {
    switch (key) {
      case 'end-all':
        return setShowEndRoomModal(true);
      case 'exit':
        return leaveRoom();
    }
  };

  if (!permissions || !isConnected) {
    return null;
  }

  return (
    <>
      {isHostUser(post) ? (
        <Dropdown menu={{ items, onClick: onMenuClick }}>
          <Button
            type="primary"
            shape="round"
            key="LeaveRoom"
            data-testid="leave_room_btn"
            css={{ borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
            // onClick={leaveRoom}
            icon={
              !isStreamKit ? (
                <ImPhoneHangUp key="hangUp" fontSize={20} />
              ) : (
                <MdExitToApp key="hangUp" fontSize={20} />
              )
            }
            danger
          />
        </Dropdown>
      ) : (
        /*<Space>
              <Tooltip title="Leave Room">
                <Button
                  type="primary"
                  shape="round"
                  key="LeaveRoom"
                  data-testid="leave_room_btn"
                  css={{ borderTopRightRadius: 0, borderBottomRightRadius: 0 }}
                  onClick={leaveRoom}
                  icon={
                    !isStreamKit ? (
                      <ImPhoneHangUp key="hangUp" fontSize={20} />
                    ) : (
                      <MdExitToApp key="hangUp" fontSize={20} />
                    )
                  }
                  danger
                />
              </Tooltip>
              <Dropdown menu={{ items, onClick: onMenuClick }} trigger={['click']}>
                <Button
                  shape="circle"
                  data-testid="leave_end_dropdown_trigger"
                  icon={<MdOutlineMoreVert fontSize={20} />}
                />
              </Dropdown>
            </Space>*/

        <Tooltip title={peerCount > 1 ? 'Leave Call' : 'End Call'}>
          <Button
            onClick={() => {
              peerCount > 1 ? leaveRoom() : setShowEndRoomModal(true);
            }}
            type="primary"
            shape="round"
            key="LeaveRoom"
            data-testid="leave_room_btn"
            icon={
              isStreamKit ? (
                <MdExitToApp fontSize={20} />
              ) : (
                <MdCallEnd key="hangUp" fontSize={20} />
              )
            }
            danger
          />
        </Tooltip>
      )}
      <Modal
        title="End Room"
        open={showEndRoomModal}
        onClose={(value) => {
          if (!value) {
            setLockRoom(false);
          }
          setShowEndRoomModal(value);
        }}
        footer={false}
      >
        <Checkbox
          id="lockRoom"
          value={lockRoom}
          onChange={() => setLockRoom(!lockRoom)}
        >
          Disable future joins
        </Checkbox>
        <Button variant="danger" onClick={endRoom} data-testid="lock_end_room">
          End Call
        </Button>
      </Modal>
    </>
  );
};
