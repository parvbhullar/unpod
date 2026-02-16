import { Button } from 'antd';
import React, { useCallback, useEffect, useState } from 'react';
import {
  CallButtonContainer,
  StyledContainer,
  VoiceOverlay,
} from './Agent.style';
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';
import {
  deleteDataApi,
  postDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { MdCall } from 'react-icons/md';
import { LiveKitRoom } from '@livekit/components-react';
import CallView from './CallView';

type AgentCardData = {
  space_token?: string;
  [key: string]: unknown;
};

type AgentProps = {
  singleCardData: AgentCardData;
};

const Agent: React.FC<AgentProps> = ({ singleCardData }) => {
  const {
    roomToken,
    updateRoomToken,
    shouldConnect,
    wsUrl,
    connect,
    disconnect,
    setConnectionMode,
  } = useAgentConnection();
  const { user } = useAuthContext();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [loadingToken, setLoadingToken] = useState(false);
  const roomRef = React.useRef<{ room_name?: string } | null>(null);
  const onStartVoice = () => {
    setLoadingToken(true);
    postDataApi(
      `core/voice/generate_room_token/public_token/`,
      infoViewActionsContext,
      {
        space_token: singleCardData.space_token,
        contact_name: user?.full_name,
      },
    )
      .then((res) => {
        const response = res as {
          data?: { token?: string; room_name?: string };
        };
        updateRoomToken(response.data?.token || null);
        setLoadingToken(false);
        roomRef.current = response.data || null;
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
        setLoadingToken(false);
      });
  };

  const handleConnect = useCallback(
    async (shouldConnect: boolean, desiredMode?: 'chat' | 'voice' | 'env') => {
      if (shouldConnect) {
        if (desiredMode) {
          setConnectionMode(desiredMode);
        }
        connect();
      } else {
        disconnect();
      }
    },
    [connect, disconnect, setConnectionMode],
  );

  useEffect(() => {
    if (roomToken) {
      handleConnect(true, 'env');
    }
  }, [roomToken, handleConnect]);

  const onRoomDisconnect = () => {
    deleteDataApi(
      `core/voice/delete_room/${roomRef.current?.room_name}/`,
      infoViewActionsContext,
    )
      .then(() => {
        // updateRoomToken(data.token);
      })
      .catch((error) => {
        void error;
      });
  };

  return (
    <StyledContainer>
      <CallButtonContainer>
        <Button
          type="primary"
          className="call-button"
          shape="round"
          icon={<MdCall />}
          loading={loadingToken}
          onClick={onStartVoice}
        >
          {!loadingToken ? 'Talk to Agent' : 'Connecting...'}
        </Button>
      </CallButtonContainer>

      {roomToken && (
        <VoiceOverlay $show={Boolean(roomToken)}>
          <LiveKitRoom
            serverUrl={wsUrl}
            token={roomToken}
            connect={shouldConnect}
            onError={(e) => {
              infoViewActionsContext.showError(e.message);
              console.error(e);
            }}
          >
            <CallView
              onConnect={(c) => {
                // Always use 'env' mode for this component
                handleConnect(c, 'env');
                if (!c) {
                  onRoomDisconnect();
                }
              }}
            />
          </LiveKitRoom>
        </VoiceOverlay>
      )}
    </StyledContainer>
  );
};

export default Agent;
