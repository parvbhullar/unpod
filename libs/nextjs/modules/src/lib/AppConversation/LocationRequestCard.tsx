'use client';
import { useState } from 'react';
import { Button } from 'antd';
import {
  CheckCircleFilled,
  CloseCircleFilled,
  EnvironmentOutlined,
} from '@ant-design/icons';
import { useIntl } from 'react-intl';
import {
  ButtonContainer,
  LocationCoords,
  LocationIcon,
  LocationRequestCard,
  RequestContent,
  RequestHeader,
  RequestReason,
  RequestSubtitle,
  RequestTitle,
  StatusContainer,
  StatusIcon,
  StatusText,
} from './LocationRequestCard.styled';

type LocationStatus =
  | 'location_request'
  | 'location_success'
  | 'location_declined';

type LocationRequestData = {
  request_id?: string | number;
  reason?: string;
  accept_text?: string;
  cancel_text?: string;
  latitude?: number;
  longitude?: number;
  accuracy?: number;
};

type LocationRequestProps = {
  data: LocationRequestData;
  onLocationResponse?: (requestId: string | number, accepted: boolean) => void;
  status?: LocationStatus;
};

const LocationRequest = ({
  data,
  onLocationResponse,
  status = 'location_request',
}: LocationRequestProps) => {
  const { formatMessage } = useIntl();
  const [localResponded, setLocalResponded] = useState(false);
  const [accepting, setAccepting] = useState(false);

  const requestId = data?.request_id;
  const reason =
    data?.reason || formatMessage({ id: 'location.defaultReason' });
  const acceptText =
    data?.accept_text || formatMessage({ id: 'location.shareLocation' });
  const cancelText =
    data?.cancel_text || formatMessage({ id: 'location.notNow' });

  const handleAccept = () => {
    if (!requestId || !onLocationResponse) return;

    setAccepting(true);
    setLocalResponded(true);
    onLocationResponse(requestId, true);
  };

  const handleDecline = () => {
    if (!requestId || !onLocationResponse) return;

    setLocalResponded(true);
    onLocationResponse(requestId, false);
  };

  // Determine states
  const isSuccess = status === 'location_success';
  const isDeclined = status === 'location_declined';
  const isLoading = localResponded && accepting;
  const showButtons = status === 'location_request' && !localResponded;
  const showStatus = localResponded || status !== 'location_request';

  // Determine icon
  const renderIcon = () => {
    if (isSuccess) return <CheckCircleFilled />;
    if (isDeclined) return <CloseCircleFilled />;
    return <EnvironmentOutlined />;
  };

  // Determine status message
  let statusMessage = '';
  let statusIcon = null;

  if (status === 'location_success') {
    statusMessage = formatMessage({ id: 'location.sharedSuccessfully' });
    statusIcon = <CheckCircleFilled />;
  } else if (status === 'location_declined') {
    statusMessage = formatMessage({ id: 'location.requestDeclined' });
    statusIcon = <CloseCircleFilled />;
  } else if (localResponded) {
    if (accepting) {
      statusMessage = formatMessage({ id: 'location.gettingLocation' });
      statusIcon = <EnvironmentOutlined />;
    } else {
      statusMessage = formatMessage({ id: 'location.requestDeclined' });
      statusIcon = <CloseCircleFilled />;
    }
  }

  return (
    <LocationRequestCard>
      <RequestHeader>
        <LocationIcon
          $success={isSuccess}
          $declined={isDeclined || (localResponded && !accepting)}
          $loading={isLoading}
        >
          {renderIcon()}
        </LocationIcon>
        <RequestContent>
          <RequestTitle>
            {formatMessage({ id: 'location.requestTitle' })}
          </RequestTitle>
          <RequestSubtitle>
            {isSuccess
              ? formatMessage({ id: 'location.shared' })
              : isDeclined
                ? formatMessage({ id: 'location.declined' })
                : isLoading
                  ? formatMessage({ id: 'location.processing' })
                  : formatMessage({ id: 'location.permissionNeeded' })}
          </RequestSubtitle>
        </RequestContent>
      </RequestHeader>

      <RequestReason>{reason}</RequestReason>

      {showButtons && (
        <ButtonContainer>
          <Button
            type="primary"
            ghost
            onClick={handleAccept}
            icon={<EnvironmentOutlined />}
          >
            {acceptText}
          </Button>
          <Button onClick={handleDecline}>{cancelText}</Button>
        </ButtonContainer>
      )}

      {showStatus && (
        <StatusContainer
          $success={isSuccess}
          $declined={isDeclined || (localResponded && !accepting)}
        >
          <StatusIcon
            $success={isSuccess}
            $declined={isDeclined || (localResponded && !accepting)}
          >
            {statusIcon}
          </StatusIcon>
          <div style={{ flex: 1 }}>
            <StatusText
              $success={isSuccess}
              $declined={isDeclined || (localResponded && !accepting)}
            >
              {statusMessage}
            </StatusText>
            {isSuccess && data?.latitude && data?.longitude && (
              <LocationCoords>
                {data.latitude.toFixed(6)}, {data.longitude.toFixed(6)}
                {data?.accuracy && ` • ±${Math.round(data.accuracy)}m`}
              </LocationCoords>
            )}
          </div>
        </StatusContainer>
      )}
    </LocationRequestCard>
  );
};

export default LocationRequest;
