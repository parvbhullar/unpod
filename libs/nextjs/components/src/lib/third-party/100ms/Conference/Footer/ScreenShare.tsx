import {
  selectIsAllowedToPublish,
  useHMSStore,
  useScreenShare,
} from '@100mslive/react-sdk';
// import { ShareScreenOptions } from './pdfAnnotator/shareScreenOptions';
import { useUISettings } from '../../AppData/useUISettings';
import { isScreenshareSupported } from '../../common/utils';
import { UI_SETTINGS } from '../../common/constants';
import { StyledContainer } from './index.styled';
import { Button, Tooltip } from 'antd';
import { MdOutlineScreenShare, MdOutlineStopScreenShare } from 'react-icons/md';

export const ScreenshareToggle = ({ css = {} }) => {
  const isAllowedToPublish = useHMSStore(selectIsAllowedToPublish);
  const isAudioOnly = useUISettings(UI_SETTINGS.isAudioOnly);

  const {
    amIScreenSharing,
    screenShareVideoTrackId: video,
    toggleScreenShare,
  } = useScreenShare();
  const isVideoScreenshare = amIScreenSharing && !!video;
  if (!isAllowedToPublish.screen || !isScreenshareSupported()) {
    return null;
  }

  return (
    <StyledContainer
      style={{
        flexDirection: 'row',
      }}
    >
      <Tooltip
        title={`${!isVideoScreenshare ? 'Start' : 'Stop'} screen sharing`}
      >
        <Button
          key="ShareScreen"
          active={!isVideoScreenshare}
          css={css}
          disabled={isAudioOnly}
          onClick={() => {
            toggleScreenShare();
          }}
          type={isVideoScreenshare ? 'primary' : 'default'}
          shape="circle"
          icon={
            isVideoScreenshare ? (
              <MdOutlineStopScreenShare fontSize={20} />
            ) : (
              <MdOutlineScreenShare fontSize={20} />
            )
          }
        />
      </Tooltip>
      {/*<ShareScreenOptions />*/}
    </StyledContainer>
  );
};
