import React, { ReactNode } from 'react';
import { TrackToggle } from '@livekit/components-react';
import { ConnectionState, Track } from 'livekit-client';
import { Button } from 'antd';
import { CloseOutlined } from '@ant-design/icons';
import styled from 'styled-components';

const FlexContainer = styled.div<{ $spaceView?: boolean }>`
  display: flex;
  height: ${({ $spaceView }) => ($spaceView ? 'auto' : '80px')};
  flex-direction: row;
  padding: ${({ $spaceView }) => ($spaceView ? '0' : '8px')};
  gap: 8px;
  align-items: center;
  border-radius: 10px;
`;

const StyledTrackToggle = styled(TrackToggle).withConfig({
  shouldForwardProp: (prop) => prop !== '$spaceView',
})<{ $spaceView?: boolean }>`
  box-sizing: border-box !important;
  padding: ${({ $spaceView }) => $spaceView && '0px'} !important;

  border: ${({ theme, $spaceView }) =>
    $spaceView ? '1px solid #a094ff' : `1px solid ${theme?.palette.primary}`};

  border-radius: 50%;
  background-color: ${({ theme, $spaceView }) =>
    $spaceView
      ? theme?.palette?.background?.default
      : theme?.palette.primary} !important;
  color: ${({ theme, $spaceView }) =>
    $spaceView ? '#a094ff' : theme?.palette.primary} !important;
  width: ${({ $spaceView }) => ($spaceView ? '32px' : '40px')} !important;
  height: ${({ $spaceView }) => ($spaceView ? '32px' : '40px')} !important;

  &:hover {
    background-color: ${({ theme, $spaceView }) =>
      $spaceView
        ? theme?.palette?.background?.default
        : theme?.palette.primary} !important;
    //border-color: #a094ff !important;
    color: ${({ $spaceView }) =>
      $spaceView ? '#a094ff' : '#ffffff'} !important;
  }
`;

const StyledButton = styled(Button).withConfig({
  shouldForwardProp: (prop) => prop !== '$spaceView',
})<{ $spaceView?: boolean }>`
  height: ${({ $spaceView }) => ($spaceView ? '32px' : '40px')} !important;
  width: ${({ $spaceView }) => ($spaceView ? '32px' : '40px')} !important;
  min-width: ${({ $spaceView }) => ($spaceView ? '32px' : '40px')} !important;
`;

type ConfigurationPanelItemProps = {
  roomState: ConnectionState;
  children?: ReactNode;
  onConnectClicked: () => void;
  spaceView?: boolean;
};

export const ConfigurationPanelItem: React.FC<ConfigurationPanelItemProps> = ({
  roomState,
  children,
  onConnectClicked,
  spaceView,
}) => {
  return (
    <FlexContainer $spaceView={spaceView}>
      <>{children}</>
      {roomState === ConnectionState.Connected && (
        <StyledTrackToggle
          source={Track.Source.Microphone}
          $spaceView={spaceView}
        />
      )}
      {roomState === ConnectionState.Connected && (
        <StyledButton
          color={spaceView ? 'default' : 'primary'}
          variant={spaceView ? 'outlined' : 'solid'}
          danger
          shape="circle"
          icon={<CloseOutlined />}
          onClick={onConnectClicked}
          $spaceView={spaceView}
        />
      )}
    </FlexContainer>
  );
};
