import React, { Fragment, useState } from 'react';
import {
  selectLocalPeerID,
  selectPermissions,
  selectSessionStore,
  selectTemplateAppData,
  selectTrackByID,
  selectVideoTrackByPeerID,
  useCustomEvent,
  useHMSActions,
  useHMSStore,
  useRemoteAVToggle,
} from '@100mslive/react-sdk';
import { useSetAppDataByKey } from '../../AppData/useUISettings';
import { useDropdownList } from '../../hooks/useDropdownList';
import { useIsFeatureEnabled } from '../../hooks/useFeatures';
import {
  APP_DATA,
  FEATURE_LIST,
  REMOTE_STOP_SCREENSHARE_TYPE,
  SESSION_STORE_KEY,
} from '../../common/constants';
import { BsFillPinAngleFill } from 'react-icons/bs';
import { VscDebugStart } from 'react-icons/vsc';
import {
  MdMic,
  MdMicOff,
  MdOutlineMoreVert,
  MdPersonRemoveAlt1,
  MdScreenShare,
  MdVideocam,
  MdVideocamOff,
} from 'react-icons/md';
import {
  RemoveMenuItem,
  StyledHeadingItem,
  StyledListContainer,
  StyledListItem,
} from './index.styled';
import { AppPopover } from '../../../../antd';
import { useInfoViewActionsContext } from '@unpod/providers';

const isSameTile = ({ trackId, videoTrackID, audioTrackID }) =>
  trackId &&
  ((videoTrackID && videoTrackID === trackId) ||
    (audioTrackID && audioTrackID === trackId));

const SpotlightActions = ({ audioTrackID, videoTrackID }) => {
  const hmsActions = useHMSActions();
  const infoViewActionsContext = useInfoViewActionsContext();

  const spotlightTrackId = useHMSStore(
    selectSessionStore(SESSION_STORE_KEY.SPOTLIGHT),
  );
  const isTileSpotlighted = isSameTile({
    trackId: spotlightTrackId,
    videoTrackID,
    audioTrackID,
  });

  const setSpotlightTrackId = (trackId) =>
    hmsActions.sessionStore
      .set(SESSION_STORE_KEY.SPOTLIGHT, trackId)
      .catch((err) => infoViewActionsContext.showError(err.description));

  return (
    <StyledListItem
      onClick={() =>
        isTileSpotlighted
          ? setSpotlightTrackId()
          : setSpotlightTrackId(videoTrackID || audioTrackID)
      }
    >
      <VscDebugStart fontSize={16} />
      <span>
        {isTileSpotlighted
          ? 'Remove from Spotlight'
          : 'Spotlight Tile for everyone'}
      </span>
    </StyledListItem>
  );
};

const PinActions = ({ audioTrackID, videoTrackID }) => {
  const [pinnedTrackId, setPinnedTrackId] = useSetAppDataByKey(
    APP_DATA.pinnedTrackId,
  );

  const isTilePinned = isSameTile({
    trackId: pinnedTrackId,
    videoTrackID,
    audioTrackID,
  });

  return (
    <StyledListItem
      onClick={() =>
        isTilePinned
          ? setPinnedTrackId()
          : setPinnedTrackId(videoTrackID || audioTrackID)
      }
    >
      <BsFillPinAngleFill fontSize={16} />
      <span>{`${isTilePinned ? 'Unpin' : 'Pin'}`} Tile for</span>
      myself
    </StyledListItem>
  );
};

const showSpotlight = process.env.REACT_APP_ENV === 'qa';

/**
 * Taking peerID as peer won't necesarilly have tracks
 */
const TileMenu = ({
  audioTrackID,
  videoTrackID,
  peerID,
  isScreenshare = false,
  ...restProps
}) => {
  const [open, setOpen] = useState(false);
  const actions = useHMSActions();
  const localPeerID = useHMSStore(selectLocalPeerID);
  const isLocal = localPeerID === peerID;
  const { removeOthers } = useHMSStore(selectPermissions);
  const {
    isAudioEnabled,
    isVideoEnabled,
    setVolume,
    toggleAudio,
    toggleVideo,
    volume,
  } = useRemoteAVToggle(audioTrackID, videoTrackID);
  const { sendEvent } = useCustomEvent({
    type: REMOTE_STOP_SCREENSHARE_TYPE,
  });

  const isPrimaryVideoTrack =
    useHMSStore(selectVideoTrackByPeerID(peerID))?.id === videoTrackID;
  const uiMode = useHMSStore(selectTemplateAppData).uiMode;
  const isInset = uiMode === 'inset';

  const isPinEnabled = useIsFeatureEnabled(FEATURE_LIST.PIN_TILE);
  const showPinAction =
    isPinEnabled &&
    (audioTrackID || (videoTrackID && isPrimaryVideoTrack)) &&
    !isInset;

  const track = useHMSStore(selectTrackByID(videoTrackID));
  const hideSimulcastLayers =
    !track?.layerDefinitions?.length || track.degraded || !track.enabled;

  useDropdownList({ open, name: 'TileMenu' });

  if (
    !(
      removeOthers ||
      toggleAudio ||
      toggleVideo ||
      setVolume ||
      showPinAction
    ) &&
    hideSimulcastLayers
  ) {
    return null;
  }

  if (isInset && isLocal) {
    return null;
  }

  const getContent = () => {
    return (
      <StyledListContainer>
        {isLocal ? (
          showPinAction && (
            <>
              <PinActions
                audioTrackID={audioTrackID}
                videoTrackID={videoTrackID}
              />
              {showSpotlight && (
                <SpotlightActions
                  audioTrackID={audioTrackID}
                  videoTrackID={videoTrackID}
                />
              )}
            </>
          )
        ) : (
          <>
            {toggleVideo ? (
              <StyledListItem
                onClick={toggleVideo}
                data-testid={
                  isVideoEnabled
                    ? 'mute_video_participant_btn'
                    : 'unmute_video_participant_btn'
                }
              >
                {isVideoEnabled ? (
                  <MdVideocam fontSize={16} />
                ) : (
                  <MdVideocamOff fontSize={16} />
                )}
                <span>{`${isVideoEnabled ? 'Mute' : 'Request Unmute'}`}</span>
              </StyledListItem>
            ) : null}
            {toggleAudio ? (
              <StyledListItem
                onClick={toggleAudio}
                data-testid={
                  isVideoEnabled
                    ? 'mute_audio_participant_btn'
                    : 'unmute_audio_participant_btn'
                }
              >
                {isAudioEnabled ? (
                  <MdMic fontSize={16} />
                ) : (
                  <MdMicOff fontSize={16} />
                )}
                <span>{`${isAudioEnabled ? 'Mute' : 'Request Unmute'}`}</span>
              </StyledListItem>
            ) : null}
            {showPinAction && (
              <>
                <PinActions
                  audioTrackID={audioTrackID}
                  videoTrackID={videoTrackID}
                />
                {showSpotlight && (
                  <SpotlightActions
                    audioTrackID={audioTrackID}
                    videoTrackID={videoTrackID}
                  />
                )}
              </>
            )}
            <SimulcastLayers trackId={videoTrackID} />
            {removeOthers ? (
              <RemoveMenuItem
                onClick={async () => {
                  try {
                    await actions.removePeer(peerID, '');
                  } catch (error) {
                    // TODO: Toast here
                  }
                }}
                data-testid="remove_participant_btn"
              >
                <MdPersonRemoveAlt1 fontSize={16} />
                <span>Remove Participant</span>
              </RemoveMenuItem>
            ) : null}

            {removeOthers && isScreenshare ? (
              <RemoveMenuItem onClick={() => sendEvent({})}>
                <MdScreenShare fontSize={16} />
                <span>Stop Screen share</span>
              </RemoveMenuItem>
            ) : null}
          </>
        )}
      </StyledListContainer>
    );
  };

  return (
    <AppPopover
      open={open}
      content={getContent()}
      onOpenChange={setOpen}
      {...restProps}
    >
      <MdOutlineMoreVert fontSize={20} />
    </AppPopover>
  );
};

const SimulcastLayers = ({ trackId }) => {
  const track = useHMSStore(selectTrackByID(trackId));
  const actions = useHMSActions();
  if (!track?.layerDefinitions?.length || track.degraded || !track.enabled) {
    return null;
  }
  const currentLayer = track.layerDefinitions.find(
    (layer) => layer.layer === track.layer,
  );
  return (
    <Fragment>
      <StyledHeadingItem>Select maximum resolution</StyledHeadingItem>
      {track.layerDefinitions.map((layer) => {
        return (
          <StyledListItem
            key={layer.layer}
            onClick={async () => {
              await actions.setPreferredLayer(trackId, layer.layer);
            }}
            style={{
              justifyContent: 'space-between',
            }}
          >
            <span
              style={{
                textTransform: 'capitalize',
                mr: '$2',
                fontWeight:
                  track.preferredLayer === layer.layer
                    ? '$semiBold'
                    : '$regular',
              }}
            >
              {layer.layer}
            </span>
            <span style={{ color: '$textMedEmp' }}>
              {layer.resolution.width}x{layer.resolution.height}
            </span>
          </StyledListItem>
        );
      })}
      <StyledListItem>
        <span>
          Currently streaming:
          <span
            style={{
              fontWeight: '$semiBold',
              textTransform: 'capitalize',
              color: '$textMedEmp',
              ml: '$2',
            }}
          >
            {currentLayer ? (
              <>
                {track.layer} ({currentLayer.resolution.width}x
                {currentLayer.resolution.height})
              </>
            ) : (
              '-'
            )}
          </span>
        </span>
      </StyledListItem>
    </Fragment>
  );
};

export default TileMenu;
