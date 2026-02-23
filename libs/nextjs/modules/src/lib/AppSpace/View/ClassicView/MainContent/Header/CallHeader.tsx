import type {ComponentType, ReactNode} from 'react';
import {useState} from 'react';
import {Flex, Tooltip, Typography} from 'antd';
import {MdCall, MdCancel, MdPhoneDisabled} from 'react-icons/md';
import {
  IoCalendarOutline,
  IoCheckmarkCircleOutline,
  IoCloseCircle,
  IoPhonePortraitOutline,
  IoSyncOutline,
} from 'react-icons/io5';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import AppSpaceCallModal from '@unpod/components/modules/AppSpaceContactCall/AppSpaceCallModal';
import {
  StyledCallTypeTag,
  StyledHeaderIcon,
  StyledHeaderSubtitle,
  StyledHeaderTitle,
  StyledStatusTag,
} from './index.styled';
import {useAppSpaceActionsContext, useAppSpaceContext,} from '@unpod/providers';
import {formatDuration, getFormattedDate, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {useMediaQuery} from 'react-responsive';
import {DesktopWidthQuery, XssMobileWidthQuery} from '@unpod/constants';
import {HiOutlinePhoneIncoming} from 'react-icons/hi';
import {FiPhoneOutgoing} from 'react-icons/fi';
import {getFirstLetter} from '@unpod/helpers/StringHelper';
import SpaceOptions from './components/SpaceOptions';
import {useIntl} from 'react-intl';

const {Text} = Typography;
///
type StatusInfo = {
  background: string;
  color: string;
  icon: ReactNode;
  label: string;
};

// Helper function to get status styling and label
export const getCallStatus = (
  status: string | undefined,
  desktopScreen: boolean,
) => {
  const statusMap: Record<string, StatusInfo> = {
    completed: {
      background: '#f6ffed',
      color: '#52c41a',
      icon: <IoCheckmarkCircleOutline size={desktopScreen ? 18 : 14}/>,
      label: 'task.completed',
    },
    connected: {
      background: '#fff7e6',
      color: '#fa8c16',
      icon: <IoPhonePortraitOutline size={desktopScreen ? 18 : 14}/>,
      label: 'task.connected',
    },
    notConnected: {
      background: '#f0f0f0',
      color: '#8c8c8c',
      icon: <MdPhoneDisabled size={desktopScreen ? 18 : 14}/>,
      label: 'task.notConnected',
    },
    failed: {
      background: '#fff1f0',
      color: '#ff4d4f',
      icon: <IoCloseCircle size={desktopScreen ? 18 : 14}/>,
      label: 'task.failed',
    },
    cancelled: {
      background: '#fafafa',
      color: '#ff4d4f',
      icon: <MdCancel size={desktopScreen ? 18 : 14}/>,
      label: 'task.cancelled',
    },
    scheduled: {
      background: '#e6f7ff',
      color: '#1890ff',
      icon: <IoCalendarOutline size={desktopScreen ? 18 : 14}/>,
      label: 'task.scheduled',
    },
    in_progress: {
      background: '#e6f4ff',
      color: '#1677ff',
      icon: (
        <IoSyncOutline
          size={desktopScreen ? 18 : 14}
          style={{animation: 'spin 1s linear infinite'}}
        />
      ),
      label: 'task.inProgress',
    },
    default: {
      background: '#fafafa',
      color: '#8c8c8c',
      icon: null,
      label: status || 'task.unknown',
    },
  };

  return (status && statusMap[status]) || statusMap.default;
};

type CallData = {
  status?: string;
  created?: string;
  input?: {
    name?: string;
    contact_number?: string;
  };
  output?: {
    duration?: number;
    scheduled_time?: string;
    call_type?: string;
    call_status?: string;
    customer?: string;
  };
  [key: string]: unknown;
};

const getUserInfo = (
  currentData: CallData | null,
  formatMessage: (msg: { id: string }) => string,
) => {
  if (!currentData) {
    return {
      icon: '',
      iconTooltip: '',
      title: '',
      time: '',
      fullDateTime: '',
    };
  }
  const customerName = currentData?.input?.name?.startsWith('sip')
    ? ''
    : currentData?.input?.name;
  const phoneNumber =
    currentData?.status === 'connected'
      ? currentData?.input?.contact_number
      : currentData?.output?.customer || currentData?.input?.contact_number;

  const time = currentData.created ? getTimeFromNow(currentData.created) : '';
  const fullDateTime = currentData.created
    ? getFormattedDate(currentData.created, 'MMM DD, YYYY [at] HH:mm', true)
    : '';

  return {
    icon: customerName || phoneNumber || formatMessage({id: 'task.unknown'}),
    iconTooltip:
      customerName ||
      phoneNumber ||
      formatMessage({id: 'task.unknownCaller'}),
    title:
      customerName ||
      phoneNumber ||
      formatMessage({id: 'task.unknownCaller'}),
    time,
    fullDateTime,
  };
};

const CallHeader = () => {
  const [visible, setVisible] = useState(false);
  const {currentSpace, activeCall} = useAppSpaceContext();
  const {callsActions} = useAppSpaceActionsContext();
  const {formatMessage} = useIntl();
  const desktopScreen = useMediaQuery(DesktopWidthQuery);
  const mobileScreen = useMediaQuery(XssMobileWidthQuery);
  const activeCallData = activeCall as CallData | null;
  const spaceName =
    typeof currentSpace?.name === 'string' ? currentSpace.name : '';
  const StyledStatusTagAny = StyledStatusTag as ComponentType<any>;

  const {icon, title, time, fullDateTime} = getUserInfo(
    activeCallData,
    formatMessage,
  );
  return (
    <div
      style={{
        justifyContent: 'space-between',
        alignItems: 'center',
        display: 'flex',
        width: '100%',
      }}
    >
      {activeCallData ? (
        <Flex gap={mobileScreen ? 6 : 10} align="center">
          <StyledHeaderIcon shape="square" size={32}>
            {getFirstLetter(icon)}
          </StyledHeaderIcon>
          <Flex vertical={true}>
            <StyledHeaderTitle level={2}>{title}</StyledHeaderTitle>
            <Tooltip title={fullDateTime}>
              <StyledHeaderSubtitle type="secondary">
                {time}
              </StyledHeaderSubtitle>
            </Tooltip>
          </Flex>
        </Flex>
      ) : (
        <Flex gap={10} align="center">
          <StyledHeaderIcon shape="square" size={32}>
            {getFirstLetter(spaceName)}
          </StyledHeaderIcon>
          <Flex vertical={true}>
            <StyledHeaderTitle level={2}>{spaceName}</StyledHeaderTitle>
          </Flex>
        </Flex>
      )}
      {activeCallData ? (
        <>
          <Flex gap={mobileScreen ? 6 : 12} align="center">
            {activeCallData?.output?.duration &&
              activeCallData?.output?.duration > 0 && (
                <Flex vertical align="flex-end">
                  <Text
                    strong
                    style={{fontSize: desktopScreen ? 12 : undefined}}
                  >
                    {formatDuration(activeCallData.output.duration)}
                  </Text>
                </Flex>
              )}
            {activeCallData?.status === 'scheduled' &&
              activeCallData?.output?.scheduled_time && (
                <Flex vertical align="flex-end">
                  <Text
                    type="secondary"
                    style={{fontSize: desktopScreen ? 11 : 10}}
                  >
                    {formatMessage({id: 'task.scheduled'})}
                  </Text>
                  <Text
                    strong
                    style={{fontSize: desktopScreen ? 12 : undefined}}
                  >
                    {getFormattedDate(
                      activeCallData.output.scheduled_time,
                      'MMM DD, HH:mm',
                      true,
                    )}
                  </Text>
                </Flex>
              )}
            {activeCallData?.output?.call_type && (
              <StyledCallTypeTag
                color={
                  activeCallData?.output?.call_type === 'inbound'
                    ? 'inbound'
                    : undefined
                }
              >
                {desktopScreen ? (
                  activeCallData?.output?.call_type === 'inbound' ? (
                    <HiOutlinePhoneIncoming size={18}/>
                  ) : (
                    <FiPhoneOutgoing size={18}/>
                  )
                ) : activeCallData?.output?.call_type === 'inbound' ? (
                  `↓ ${formatMessage({id: 'common.incoming'})}`
                ) : (
                  `↑ ${formatMessage({id: 'common.outgoing'})}`
                )}
              </StyledCallTypeTag>
            )}
            {activeCallData?.status &&
              (() => {
                const statusInfo = getCallStatus(
                  activeCallData.output?.call_status
                    ? activeCallData.output.call_status
                    : activeCallData.status,
                  desktopScreen,
                );
                return (
                  <StyledStatusTagAny
                    $bg={statusInfo.background}
                    $color={statusInfo.color}
                  >
                    {statusInfo.icon}
                    {!desktopScreen && formatMessage({id: statusInfo.label})}
                  </StyledStatusTagAny>
                );
              })()}
            {currentSpace?.content_type === 'contact' && (
              <AppHeaderButton
                type="primary"
                shape={!desktopScreen ? 'round' : 'circle'}
                icon={
                  <span className="anticon" style={{verticalAlign: 'middle'}}>
                    <MdCall fontSize={!desktopScreen ? 16 : 22}/>
                  </span>
                }
                onClick={() => setVisible(true)}
              >
                {!desktopScreen && formatMessage({id: 'spaceHeader.call'})}
              </AppHeaderButton>
            )}
          </Flex>
          <AppSpaceCallModal
            open={visible}
            setOpen={setVisible}
            idKey="document_id"
            from="call"
            onFinishSchedule={() => {
              (callsActions as { reCallAPI: () => void }).reCallAPI();
              // setActiveCall(data);
            }}
          />
        </>
      ) : (
        <SpaceOptions/>
      )}
    </div>
  );
};

export default CallHeader;
