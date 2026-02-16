import React from 'react';
import {
  BarVisualizer,
  TrackReferenceOrPlaceholder,
} from '@livekit/components-react';
import styled from 'styled-components';
import { ConnectionState } from 'livekit-client';

const AudioTileContainer = styled.div`
  display: flex;
  height: 60px;
  color: #333333;
  position: relative;
  width: 100%;
`;

const StateOverlay = styled.div<{ $spaceView?: boolean }>`
  height: 60px;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  position: absolute;
  color: #333333;

  text-transform: capitalize;
  font-size: ${({ $spaceView }) => ($spaceView ? '18px' : '124px')};
  background-color: #ffffff99;
  display: flex;
  justify-content: center;
  align-items: center;
`;

type AudioOutputTileProps = {
  trackRef?: TrackReferenceOrPlaceholder;
  state?: string;
  spaceView?: boolean;};

const AudioOutputTile: React.FC<AudioOutputTileProps> = ({
  trackRef,
  state,
  spaceView,
}) => {
  return (
    <AudioTileContainer>
      <BarVisualizer
        state={state as any}
        trackRef={trackRef}
        barCount={spaceView ? 12 : undefined}
        options={{ minHeight: 30, maxHeight: spaceView ? 45 : 60 }}
      />

      {state === ConnectionState.Connecting && (
        <StateOverlay $spaceView={spaceView}>{state}...</StateOverlay>
      )}
    </AudioTileContainer>
  );
};

export default AudioOutputTile;
