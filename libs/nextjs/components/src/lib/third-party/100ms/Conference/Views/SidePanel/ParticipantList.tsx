import React, { Fragment, useCallback, useEffect, useState } from 'react';
import { useDebounce } from 'react-use';
import {
  selectAudioTrackByPeerID,
  selectLocalPeerID,
  selectPeerCount,
  selectPeerMetadata,
  selectPermissions,
  useHMSActions,
  useHMSStore,
  useParticipants,
} from '@100mslive/react-sdk';

import { ConnectionIndicator } from '../../Connection/ConnectionIndicator';
import { RoleChangeModal } from '../RoleChangeModal';
import { TbHandOff } from 'react-icons/tb';
// import { ParticipantFilter } from './ParticipantFilter';
import {
  useIsSidepaneTypeOpen,
  useSidepaneToggle,
} from '../../../AppData/useSidepane';
// import { isInternalRole } from '../../../common/utils';
import { SIDE_PANE_OPTIONS } from '../../../common/constants';
import { Avatar, Button, Dropdown, Input, Slider, Space } from 'antd';
import { StyledContainer } from './index.styled';
// import { FiUserMinus } from 'react-icons/fi';
import { MdMoreVert, MdPeople } from 'react-icons/md';
import { getFirstLetter } from '@unpod/helpers/StringHelper';
import { isInternalRole } from '../../../common/utils';
import { HiOutlineSpeakerWave } from 'react-icons/hi2';

export const ParticipantList = () => {
  const [filter, setFilter] = useState();
  const { participants, isConnected, peerCount, rolesWithParticipants } =
    useParticipants(filter);
  const [selectedPeerId, setSelectedPeerId] = useState(null);
  const onSearch = useCallback((value) => {
    setFilter((filterValue) => {
      if (!filterValue) {
        filterValue = {};
      }
      filterValue.search = value;
      return { ...filterValue };
    });
  }, []);
  if (peerCount === 0) {
    return null;
  }

  return (
    <Fragment>
      <StyledContainer direction="column" css={{ size: '100%' }}>
        {!filter?.search && participants.length === 0 ? null : (
          <ParticipantSearch onSearch={onSearch} />
        )}
        {participants.length === 0 && (
          <StyledContainer
            style={{
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              padding: '8px 0',
            }}
          >
            <div>
              {!filter ? 'No participants' : 'No matching participants'}
            </div>
          </StyledContainer>
        )}
        <VirtualizedParticipants
          participants={participants}
          isConnected={isConnected}
          setSelectedPeerId={setSelectedPeerId}
        />
      </StyledContainer>
      {selectedPeerId && (
        <RoleChangeModal
          peerId={selectedPeerId}
          onOpenChange={(value) => {
            !value && setSelectedPeerId(null);
          }}
        />
      )}
    </Fragment>
  );
};

export const ParticipantCount = () => {
  const peerCount = useHMSStore(selectPeerCount);
  const toggleSidepane = useSidepaneToggle(SIDE_PANE_OPTIONS.PARTICIPANTS);
  const isParticipantsOpen = useIsSidepaneTypeOpen(
    SIDE_PANE_OPTIONS.PARTICIPANTS
  );
  useEffect(() => {
    if (isParticipantsOpen && peerCount === 0) {
      toggleSidepane();
    }
  }, [isParticipantsOpen, peerCount, toggleSidepane]);

  if (peerCount === 0) {
    return null;
  }
  return (
    <Button
      style={{
        width: 'auto',
        padding: 16,
        height: 'auto',
      }}
      onClick={() => {
        if (peerCount > 0) {
          toggleSidepane();
        }
      }}
      active={!isParticipantsOpen}
      data-testid="participant_list"
      icon={<MdPeople />}
    >
      {peerCount}
    </Button>
  );
};

function itemKey(index, data) {
  return data.participants[index].id;
}

const VirtualizedParticipants = ({
  participants,
  isConnected,
  setSelectedPeerId,
}) => {
  return (
    <div
      style={{
        flex: '1 1 0',
      }}
    >
      {participants.map((participant, index) => {
        return (
          <Participant
            peer={participant}
            isConnected={isConnected}
            setSelectedPeerId={setSelectedPeerId}
          />
        );
      })}
    </div>
  );
};

const Participant = ({ peer, isConnected, setSelectedPeerId }) => {
  const metaData = useHMSStore(selectPeerMetadata(peer.id));
  return (
    <StyledContainer
      key={peer.id}
      style={{
        flexDirection: 'row',
        width: '100%',
        paddingTop: 16,
        paddingRight: 16,
        paddingLeft: 16,
      }}
      align="center"
      data-testid={'participant_' + peer.name}
    >
      <Avatar
        src={metaData?.user_detail?.profile_picture}
        style={{
          marginRight: 16,
          fontSize: 14,
          backgroundColor: metaData?.user_detail?.profile_color || '#1890ff',
        }}
      >
        {getFirstLetter(peer.name)}
      </Avatar>
      <StyledContainer direction="column" css={{ flex: '1 1 0' }}>
        <div style={{ fontWeight: 500 }}>{peer.name}</div>
        <div>{peer.roleName}</div>
      </StyledContainer>
      {isConnected && (
        <ParticipantActions
          peerId={peer.id}
          role={peer.roleName}
          onSettings={() => {
            setSelectedPeerId(peer.id);
          }}
        />
      )}
    </StyledContainer>
  );
};

/**
 * shows settings to change for a participant like changing their role
 */
const ParticipantActions = React.memo(({ onSettings, peerId, role }) => {
  const isHandRaised = useHMSStore(selectPeerMetadata(peerId))?.isHandRaised;
  const canChangeRole = useHMSStore(selectPermissions)?.changeRole;
  const audioTrack = useHMSStore(selectAudioTrackByPeerID(peerId));
  const localPeerId = useHMSStore(selectLocalPeerID);
  const canChangeVolume = peerId !== localPeerId && audioTrack;
  const shouldShowMoreActions = canChangeRole || canChangeVolume;

  return (
    <StyledContainer
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        flexShrink: 0,
        fontSize: 20,
      }}
    >
      <ConnectionIndicator peerId={peerId} />
      {isHandRaised && <TbHandOff />}
      {shouldShowMoreActions && !isInternalRole(role) && (
        <ParticipantMoreActions
          onRoleChange={onSettings}
          peerId={peerId}
          role={role}
        />
      )}
    </StyledContainer>
  );
});

const ParticipantMoreActions = ({ onRoleChange, peerId }) => {
  const { changeRole: canChangeRole, removeOthers: canRemoveOthers } =
    useHMSStore(selectPermissions);
  const localPeerId = useHMSStore(selectLocalPeerID);
  const isLocal = localPeerId === peerId;
  const actions = useHMSActions();
  const audioTrack = useHMSStore(selectAudioTrackByPeerID(peerId));

  const getItems = () => {
    let items = [];
    if (canChangeRole) {
      items.push({
        label: 'Change Role',
        key: 'changeRole',
      });
    }
    const volume = ParticipantVolume({ peerId });
    if (volume) {
      items.push({
        label: volume,
        key: 'settings',
      });
    }
    if (!isLocal && canRemoveOthers) {
      items.push({
        label: 'Remove Participant',
        key: 'removeParticipant',
      });
    }
    return items;
  };

  const removeParticipant = async () => {
    await actions.removePeer(peerId, '');
  };

  const onClick = ({ key }) => {
    switch (key) {
      case 'changeRole':
        return onRoleChange(peerId);
      case 'removeParticipant':
        return removeParticipant();
    }
  };
  return (
    <Dropdown
      menu={{ items: getItems(), onClick: onClick }}
      trigger={['click']}
    >
      <MdMoreVert />
    </Dropdown>
  );
};

const ParticipantVolume = ({ peerId }) => {
  const audioTrack = useHMSStore(selectAudioTrackByPeerID(peerId));
  const localPeerId = useHMSStore(selectLocalPeerID);
  const hmsActions = useHMSActions();
  // No volume control for local peer or non audio publishing role
  if (peerId === localPeerId || !audioTrack) {
    return null;
  }

  return (
    <StyledContainer style={{ width: '100%', minWidth: 220 }}>
      <Space>
        <HiOutlineSpeakerWave />
        <span>Volume{audioTrack.volume ? `(${audioTrack.volume})` : ''}</span>
      </Space>
      <Slider
        style={{ marginTop: '0.5rem' }}
        step={5}
        value={audioTrack?.volume}
        onChange={(value) => {
          console.log('value', value);
          hmsActions.setVolume(value, audioTrack?.id);
        }}
      />
    </StyledContainer>
  );
};

export const ParticipantSearch = ({ onSearch, placeholder }) => {
  const [value, setValue] = React.useState('');
  useDebounce(
    () => {
      onSearch(value);
    },
    300,
    [value, onSearch]
  );
  return (
    <div style={{ margin: ' 0 16px', marginTop: 12, position: 'relative' }}>
      <Input
        type="text"
        placeholder={placeholder || 'Find what you are looking for'}
        style={{ width: '100%', paddingLeft: 14 }}
        value={value}
        onKeyDown={(event) => {
          event.stopPropagation();
        }}
        onChange={(event) => {
          setValue(event.currentTarget.value);
        }}
        autoComplete="off"
        aria-autocomplete="none"
      />
    </div>
  );
};
