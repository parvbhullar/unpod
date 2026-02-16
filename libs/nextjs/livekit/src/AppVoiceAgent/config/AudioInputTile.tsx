import React from 'react';
import {
  BarVisualizer,
  TrackReferenceOrPlaceholder,
} from '@livekit/components-react';
import styled from 'styled-components';
import CircularVisualizer from './CircularVisualizer';

const StyledBarVisualizerContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 2px;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  --lk-va-bar-width: 5px;
  --lk-va-bar-gap: 5px;
  --lk-fg: ${({ theme }) => theme?.palette.primary};
`;
const StyledDiv = styled.div`
  width: 100%;
  height: 100px;
`;

type AudioInputTileConfig = {
  circular?: boolean;
  local?: Record<string, unknown>;};

type AudioInputTileProps = {
  trackRef?: TrackReferenceOrPlaceholder;
  config?: AudioInputTileConfig;};

export const AudioInputTile: React.FC<AudioInputTileProps> = ({
  trackRef,
  config,
}) => {
  if (config?.circular) {
    return (
      <CircularVisualizer
        trackRef={trackRef}
        barCount={50}
        config={config.local}
        options={{ minHeight: 3, maxHeight: 50 }}
      />
    );
  }
  return (
    <StyledDiv>
      <StyledBarVisualizerContainer>
        <BarVisualizer
          trackRef={trackRef}
          barCount={50}
          options={{ minHeight: 3, maxHeight: 50 }}
        />
      </StyledBarVisualizerContainer>
    </StyledDiv>
  );
};
