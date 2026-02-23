import {useEffect, useState} from 'react';
import {
  selectAppData,
  selectIsConnectedToRoom,
  selectPermissions,
  useHMSActions,
  useHMSStore,
  useRecordingStreaming,
} from '@100mslive/react-sdk';
// import GoLiveButton from "../GoLiveButton";
// import { ResolutionInput } from "../Streaming/ResolutionInput";
// import { getResolution } from "../Streaming/RTMPStreaming";
import {ToastManager} from '../Toast/ToastManager';
// import {
//   AdditionalRoomState,
//   getRecordingText,
// } from './AdditionalRoomState';
import {useSetAppDataByKey} from '../AppData/useUISettings';
import {APP_DATA, RTMP_RECORD_DEFAULT_RESOLUTION} from '../common/constants';
import {Button, Space, Tooltip} from 'antd';
import {BsRecordCircle, BsRecordFill} from 'react-icons/bs';
import {getDataApi, useInfoViewActionsContext, useOrgActionContext} from '@unpod/providers';
import {useStreamContext} from '../StreamContextProvider';

// export const LiveStatus = () => {
//   const { isHLSRunning, isRTMPRunning } = useRecordingStreaming();
//   if (!isHLSRunning && !isRTMPRunning) {
//     return null;
//   }
//   return (
//     <Flex align="center">
//       <Box css={{ w: '$4', h: '$4', r: '$round', bg: '$error', mr: '$2' }} />
//       <Text>
//         Live
//         <Text as="span" css={{ '@md': { display: 'none' } }}>
//           &nbsp;with {isHLSRunning ? 'HLS' : 'RTMP'}
//         </Text>
//       </Text>
//     </Flex>
//   );
// };

// export const RecordingStatus = () => {
//   const {
//     isBrowserRecordingOn,
//     isServerRecordingOn,
//     isHLSRecordingOn,
//     isRecordingOn,
//   } = useRecordingStreaming();
//   const permissions = useHMSStore(selectPermissions);
//
//   if (
//     !isRecordingOn ||
//     // if only browser recording is enabled, stop recording is shown
//     // so no need to show this as it duplicates
//     [
//       permissions?.browserRecording,
//       !isServerRecordingOn,
//       !isHLSRecordingOn,
//       isBrowserRecordingOn,
//     ].every((value) => !!value)
//   ) {
//     return null;
//   }
//   return (
//     <Tooltip
//       title={getRecordingText({
//         isBrowserRecordingOn,
//         isServerRecordingOn,
//         isHLSRecordingOn,
//       })}
//     >
//       <Button icon={<BsRecordCircle fontSize={20} />} />
//     </Tooltip>
//   );
// };

export const StartRecording = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {post} = useStreamContext();
  const {setCallRecording} = useOrgActionContext();
  const permissions = useHMSStore(selectPermissions);
  const recordingUrl = useHMSStore(selectAppData(APP_DATA.recordingUrl));
  const [resolution] = useState(RTMP_RECORD_DEFAULT_RESOLUTION);
  const [recordingStarted, setRecordingState] = useSetAppDataByKey(
    APP_DATA.recordingStarted
  );
  const {isBrowserRecordingOn, isStreamingOn, isHLSRunning} =
    useRecordingStreaming();
  const hmsActions = useHMSActions();

  useEffect(() => {
    setCallRecording(isBrowserRecordingOn);
  }, [isBrowserRecordingOn]);

  if (!permissions?.browserRecording || isHLSRunning) {
    return null;
  }

  const toggleRecording = async () => {
    if (isBrowserRecordingOn) {
      try {
        await hmsActions.stopRTMPAndRecording();
        getDataApi(
          `threads/${post.slug}/hms/recording/stop/`,
          infoViewActionsContext
        )
          .then((res) => {
            console.log(res);
          })
          .catch((error) => {
            console.log(error);
            ToastManager.addToast({
              title: error.message,
              variant: 'error',
            });
          });
      } catch (error) {
        ToastManager.addToast({
          title: error.message,
          variant: 'error',
        });
      }
    } else {
      try {
        setRecordingState(true);
        await hmsActions.startRTMPOrRecording({
          meetingURL: recordingUrl,
          resolution: getResolution(resolution),
          record: true,
        });
        getDataApi(
          `threads/${post.slug}/hms/recording/start/`,
          infoViewActionsContext
        )
          .then((res) => {
            console.log(res);
          })
          .catch((error) => {
            console.log(error);
            ToastManager.addToast({
              title: error.message,
              variant: 'error',
            });
          });
      } catch (error) {
        if (error.message.includes('stream already running')) {
          ToastManager.addToast({
            title: 'Recording already running',
            variant: 'error',
          });
        } else {
          ToastManager.addToast({
            title: error.message,
            variant: 'error',
          });
        }
        setRecordingState(false);
      }
    }
  };

  return (
    <Tooltip
      title={isBrowserRecordingOn ? 'Stop Recording' : 'Start Recording'}
    >
      <Button
        data-testid="start_recording"
        variant="standard"
        disabled={recordingStarted || isStreamingOn}
        type={isBrowserRecordingOn ? 'primary' : 'default'}
        shape="circle"
        icon={
          isBrowserRecordingOn ? (
            <BsRecordFill fontSize={20}/>
          ) : (
            <BsRecordCircle fontSize={20}/>
          )
        }
        onClick={toggleRecording}
      />
    </Tooltip>
  );
};

function getResolution(recordingResolution) {
  const resolution = {};
  if (recordingResolution.width) {
    resolution.width = recordingResolution.width;
  }
  if (recordingResolution.height) {
    resolution.height = recordingResolution.height;
  }
  if (Object.keys(resolution).length > 0) {
    return resolution;
  }
}

export const StreamActions = () => {
  const isConnected = useHMSStore(selectIsConnectedToRoom);

  return (
    <Space>
      {/*<AdditionalRoomState />*/}
      {/*<RecordingStatus />*/}
      {isConnected ? <StartRecording/> : null}
    </Space>
  );
};
