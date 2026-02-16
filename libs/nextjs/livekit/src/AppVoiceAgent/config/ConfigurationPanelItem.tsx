import { ConnectionState, Track } from 'livekit-client';
import Button from '../../components/Button';
import styled from 'styled-components';
import { GrClose } from 'react-icons/gr';
import type { ReactNode } from 'react';

import { TrackToggle } from './TrackToggle';

const FlexContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
  border-radius: 10px;
`;

const StyledTrackToggle = styled(TrackToggle)`
  border: ${({ theme }) => `1px solid ${theme?.palette.primary}`};
  border-radius: 50%;
  height: 40px !important;
  width: 40px !important;
  background-color: ${({ theme }) => theme?.palette.primary} !important;
  color: white;

  &:hover {
    background-color: ${({ theme }) => theme?.palette.primary} !important;
  }
`;

type ConfigurationPanelItemProps = {
  roomState: ConnectionState;
  children?: ReactNode;
  onConnectClicked: () => void;
};

export const ConfigurationPanelItem = ({
  roomState,
  children,
  onConnectClicked,
}: ConfigurationPanelItemProps) => {
  return (
    <FlexContainer>
      <>{children}</>
      {roomState === ConnectionState.Connected && (
        <StyledTrackToggle source={Track.Source.Microphone} />
      )}
      {roomState === ConnectionState.Connected && (
        <Button
          variant="primary"
          danger
          shape="circle"
          icon={<GrClose />}
          onClick={onConnectClicked}
        />
      )}
    </FlexContainer>
  );
};
