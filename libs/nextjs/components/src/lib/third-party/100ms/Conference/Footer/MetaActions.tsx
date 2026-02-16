import {
  selectIsConnectedToRoom,
  selectPeerCount,
  useHMSStore,
} from '@100mslive/react-sdk';
import { useIsFeatureEnabled } from '../../hooks/useFeatures';
import { useMyMetadata } from '../../hooks/useMetadata';
import { FEATURE_LIST } from '../../common/constants';
import { Badge, Button, Space, Tooltip } from 'antd';
import { GiBackForth } from 'react-icons/gi';
import { TbHandOff, TbHandStop } from 'react-icons/tb';
import React from 'react';
import AppDrawer from '../../../../antd/AppDrawer';
import { ParticipantList } from '../Views/SidePanel/ParticipantList';
import { FiUsers } from 'react-icons/fi';
import { globalTheme } from '@unpod/mix';

const MetaActions = ({ isMobile = false }) => {
  const isConnected = useHMSStore(selectIsConnectedToRoom);
  const peerCount = useHMSStore(selectPeerCount);
  const { isHandRaised, isBRBOn, toggleHandRaise, toggleBRB } = useMyMetadata();
  const isHandRaiseEnabled = useIsFeatureEnabled(FEATURE_LIST.HAND_RAISE);
  const isBRBEnabled = useIsFeatureEnabled(FEATURE_LIST.BRB);
  const [showParticipants, setShowParticipants] = React.useState(false);
  const [showThreads, setShowThreads] = React.useState(false);

  if (!isConnected || (!isHandRaiseEnabled && !isBRBEnabled)) {
    return null;
  }

  return (
    <>
      <Space diection="horizontal">
        <Tooltip title="Participant">
          <Badge
            count={peerCount}
            color={globalTheme.palette.primary}
            offset={[-5, 3]}
          >
            <Button
              shape="circle"
              onClick={() => setShowParticipants(true)}
              icon={<FiUsers fontSize={20} />}
            />
          </Badge>
        </Tooltip>
        {/*<Tooltip title="Chat">
          <Button
            onClick={() => setShowThreads(true)}
            icon={<BsChatSquareDots fontSize={20} />}
          />
        </Tooltip>*/}
        {isHandRaiseEnabled && (
          <Tooltip title={`${!isHandRaised ? 'Raise' : 'Unraise'} hand`}>
            <Button
              onClick={toggleHandRaise}
              active={!isHandRaised}
              type={isHandRaised ? 'primary' : 'default'}
              shape="circle"
              data-testid={`${
                isMobile ? 'raise_hand_btn_mobile' : 'raise_hand_btn'
              }`}
              icon={
                isHandRaised ? (
                  <TbHandOff fontSize={20} />
                ) : (
                  <TbHandStop fontSize={20} />
                )
              }
            />
          </Tooltip>
        )}
        {isBRBEnabled && (
          <Tooltip title={`${isBRBOn ? `I'm back` : `I'll be right back`}`}>
            <Button
              onClick={toggleBRB}
              active={!isBRBOn}
              type={isBRBOn ? 'primary' : 'default'}
              shape="circle"
              data-testid="brb_btn"
              icon={<GiBackForth fontSize={20} />}
            />
          </Tooltip>
        )}
      </Space>

      <AppDrawer
        title={`Participants (${peerCount})`}
        open={showParticipants}
        onClose={() => setShowParticipants(false)}
      >
        <ParticipantList />
      </AppDrawer>

      <AppDrawer
        title="Chat"
        open={showThreads}
        onClose={() => setShowThreads(false)}
      >
        <div>Chat</div>
      </AppDrawer>
    </>
  );
};

export default MetaActions;
