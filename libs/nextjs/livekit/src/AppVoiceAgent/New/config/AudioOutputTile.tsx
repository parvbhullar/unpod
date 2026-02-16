import React from 'react';
import styled from 'styled-components';
import CircularVisualizer from './CircularVisualizer';
import { ConnectionState } from 'livekit-client';
import { BarVisualizer } from './BarVisualizer';
import { TrackReferenceOrPlaceholder } from '@livekit/components-react';

const AudioTileContainer = styled.div`
    display: flex;
    height: 70px !important;
    color: #333333;
    align-items: center;
    justify-content: center;
    position: relative;
    width: 100%;
`;

const StateOverlay = styled.div`
    height: 70px;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    position: absolute;
    color: #333333;

    text-transform: capitalize;
    font-size: 24px;
    background-color: #FFFFFF99;
    display: flex;
    justify-content: center;
    align-items: center;
`;

interface AudioOutputTileConfig {
  circular?: boolean;
  agent?: Record<string, unknown>;
}

interface AudioOutputTileProps {
  trackRef?: TrackReferenceOrPlaceholder;
  state?: string;
  config?: AudioOutputTileConfig;
}

const AudioOutputTile: React.FC<AudioOutputTileProps> = ({ trackRef, state, config }) => {
  if (config?.circular) {
    return (
      <CircularVisualizer
        state={state}
        config={config?.agent}
        trackRef={trackRef}
        barCount={50}
        options={{ minHeight: 3, maxHeight: 50 }}
      />
    );
  }
  return (
    <AudioTileContainer>
      <BarVisualizer
        state={state}
        barCount={45}
        trackRef={trackRef}
        options={{ minHeight: 40, maxHeight: 70 }}
      />

      {state === ConnectionState.Connecting && (
        <StateOverlay>{state}...</StateOverlay>
      )}
    </AudioTileContainer>
  );
};

export default AudioOutputTile;
