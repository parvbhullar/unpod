import {selectLocalPeerRoleName, useHMSStore} from '@100mslive/react-sdk';
import {useHLSViewerRole} from '../../AppData/useUISettings';
import {useIsFeatureEnabled} from '../../hooks/useFeatures';
import {useWhiteboardMetadata} from './useWhiteboardMetadata';
import {FEATURE_LIST} from '../../common/constants';
import {Button, Tooltip} from 'antd';
import {MdOutlineDraw} from 'react-icons/md';

export const ToggleWhiteboard = () => {
  const {
    whiteboardEnabled,
    whiteboardOwner: whiteboardActive,
    amIWhiteboardOwner,
    toggleWhiteboard,
  } = useWhiteboardMetadata();
  const hlsViewerRole = useHLSViewerRole();
  const localPeerRole = useHMSStore(selectLocalPeerRoleName);
  const isFeatureEnabled = useIsFeatureEnabled(FEATURE_LIST.WHITEBOARD);

  // if (
  //   !whiteboardEnabled ||
  //   localPeerRole === hlsViewerRole ||
  //   !isFeatureEnabled
  // ) {
  //   return null;
  // }

  return (
    <Tooltip
      title={`${
        whiteboardActive
          ? amIWhiteboardOwner
            ? `Stop whiteboard`
            : `Can't stop whiteboard`
          : 'Start whiteboard'
      }`}
      key="whiteboard"
    >
      <Button
        onClick={toggleWhiteboard}
        type={whiteboardActive ? 'primary' : 'default'}
        shape="circle"
        // disabled={whiteboardActive && !amIWhiteboardOwner}
        data-testid="white_board_btn"
        icon={<MdOutlineDraw fontSize={20}/>}
      />
    </Tooltip>
  );
};
