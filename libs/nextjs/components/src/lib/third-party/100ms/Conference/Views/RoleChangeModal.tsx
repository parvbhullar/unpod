import React, {useState} from 'react';
import {selectPeerByID, useHMSActions, useHMSStore,} from '@100mslive/react-sdk';
import {useFilteredRoles} from '../../common/hooks';
import {Button, Modal, Select, Space, Tooltip} from 'antd';

const PeerName = ({children, maxWidth, ref, ...rest}) => (
  <strong
    {...rest}
    ref={ref}
    css={{
      display: 'inline-block',
      fontWeight: 500,
      color: 'inherit',
    }}
  >
    {children}
  </strong>
);

export const RoleChangeModal = ({peerId, onOpenChange}) => {
  const peer = useHMSStore(selectPeerByID(peerId));
  const roles = useFilteredRoles();
  const [selectedRole, setRole] = useState(peer?.roleName);
  const [requestPermission, setRequestPermission] = useState(false);
  const hmsActions = useHMSActions();
  const [peerNameRef, setPeerNameRef] = useState();
  if (!peer) {
    return null;
  }
  const peerNameMaxWidth = 200;
  return (
    <Modal
      title="Change Role"
      open={peerId}
      centered
      closeIcon={false}
      maskClosable={false}
      style={{
        maxWidth: '400px',
      }}
      onCancel={() => onOpenChange(false)}
      footer={
        <Space>
          <Button onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            type="primary"
            onClick={async () => {
              await hmsActions.changeRole(
                peerId,
                selectedRole,
                peer.isLocal ? true : !requestPermission
              );
              onOpenChange(false);
            }}
          >
            Change
          </Button>
        </Space>
      }
    >
      <p
        css={{
          mt: 12,
          mb: 24,
          display: 'flex',
          flexWrap: 'wrap',
          columnGap: '4px',
        }}
      >
        Change the role of
        {peerNameRef && peerNameRef.clientWidth === peerNameMaxWidth ? (
          <Tooltip title={peer.name} side="top">
            <PeerName ref={setPeerNameRef} maxWidth={peerNameMaxWidth}>
              {peer.name}
            </PeerName>
          </Tooltip>
        ) : (
          <PeerName ref={setPeerNameRef} maxWidth={peerNameMaxWidth}>
            {peer.name}
          </PeerName>
        )}
        to
      </p>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          width: '100%',
          justifyContent: 'space-between',
        }}
      >
        <Select
          defaultValue={selectedRole}
          style={{width: '100%'}}
          onChange={setRole}
          options={roles.map((role) => ({
            label: (
              <span
                style={{
                  textTransform: 'capitalize',
                }}
              >
                {role}
              </span>
            ),
            value: role,
          }))}
        />
      </div>
      {/* {!peer.isLocal && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            width: '100%',
            justifyContent: 'space-between',
          }}
        >
          <span
            htmlFor="requestRoleChangePermission"
            css={{ cursor: 'pointer' }}
          >
            Request Permission
          </span>
          <Checkbox
            id="requestRoleChangePermission"
            checked={requestPermission}
            onCheckedChange={(value) => setRequestPermission(value)}
          />
          <Checkbox.Root
            checked={requestPermission}
            onCheckedChange={(value) => setRequestPermission(value)}
            id="requestRoleChangePermission"
            data-testid="force_role_change_checkbox"
          >
            <Checkbox.Indicator>
              <CheckIcon width={16} height={16} />
            </Checkbox.Indicator>
          </Checkbox.Root>
        </div>
      )}*/}
    </Modal>
  );
};
