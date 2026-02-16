import React from 'react';
import styled, { keyframes } from 'styled-components';
import {
  TrackReferenceOrPlaceholder,
  useMaybeTrackRefContext,
  useMultibandTrackVolume,
} from '@livekit/components-react';
import { useBarAnimator } from './useBarAnimator';

// Animation for the outer ring
const rotate = keyframes`
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
`;

const VisualizerContainer = styled.div`
  position: relative;
  width: 200px;
  height: 200px;
  //background-color: gray;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const Avatar = styled.div<{ color?: string }>`
  width: 140px;
  height: 140px;
  border-radius: 50%;
  margin-top: 5px;
  background: linear-gradient(
    to top,
    ${({ color }) => `${color ? color : '#6a5acd'}`},
    ${({ color }) => `${color ? color : '#8a2be2'}`}
  );
  z-index: 2;
  box-shadow: 0 0 10px ${({ color }) => `${color ? color : '#6a5acd'}`};
  overflow: hidden;

  img {
    width: 140px;
    height: 140px;
  }
`;

const OuterCircle = styled.div<{ color?: string }>`
  position: absolute;
  width: 160px;
  margin-top: 5px;
  height: 160px;
  border-radius: 50%;
  border: 3px solid
    ${({ color }) => `${color ? color : 'rgba(150, 100, 255, 0.6)'}`};
  //animation: ${rotate} 8s linear infinite;
`;

const Bar = styled.div<{ color?: string }>`
  position: absolute;
  width: 3px;
  background: linear-gradient(
    to top,
    ${({ color }) => `${color ? color : '#6a5acd'}`},
    ${({ color }) => `${color ? color : '#8a2be2'}`}
  );
  border-radius: 10px 10px 0 0;
  transform-origin: center bottom;
  transition:
    height 0.1s ease-out,
    background 0.3s ease-in-out;
`;

const sequencerIntervals = new Map([
  ['connecting', 2000],
  ['initializing', 2000],
  ['listening', 500],
  ['thinking', 150],
]);

const getSequencerInterval = (state: string | undefined, barCount: number) => {
  if (state === undefined) {
    return 1000;
  }
  let interval = sequencerIntervals.get(state);
  if (interval) {
    switch (state) {
      case 'connecting':
        // case 'thinking':
        interval /= barCount;
        break;

      default:
        break;
    }
  }
  return interval;
};

type CircularVisualizerConfig = {
  color?: string;
  activeColor?: string;
  image?: string;};

type CircularVisualizerProps = {
  config?: CircularVisualizerConfig;
  state?: string;
  trackRef?: TrackReferenceOrPlaceholder;
  barCount?: number;
  options?: {
    minHeight?: number;
    maxHeight?: number;
  };};

const CircularVisualizer: React.FC<CircularVisualizerProps> = ({
  config,
  state,
  trackRef,
  barCount = 40,
  options,
}) => {
  let trackReference = useMaybeTrackRefContext();

  if (trackRef) {
    trackReference = trackRef;
  }

  const volumeBands = useMultibandTrackVolume(trackReference, {
    bands: barCount,
    loPass: 100,
    hiPass: 200,
  });

  const highlightedIndices = useBarAnimator(
    state,
    barCount,
    getSequencerInterval(state, barCount) ?? 100,
  );
  const minHeight = options?.minHeight ?? 3;
  const maxHeight = options?.maxHeight ?? 50;

  return (
    <VisualizerContainer>
      <Avatar color={config?.color}>
        <img src={config?.image || '/images/design-team.png'} />
      </Avatar>
      <OuterCircle color={config?.color} />
      {volumeBands.map((height, idx) => {
        const angle = (idx / barCount) * 360;
        const isActive = highlightedIndices.includes(idx);
        const barHeight = Math.min(
          maxHeight,
          Math.max(minHeight, height * maxHeight),
        );
        return (
          <Bar
            key={idx}
            color={config?.activeColor}
            style={{
              height: `${barHeight}px`,
              transform: `rotate(${angle}deg) translateY(-80px)`,
              background: isActive
                ? `linear-gradient(to top, ${
                    config?.activeColor ? config.activeColor : '#ff4500'
                  }, ${config?.activeColor ? config.activeColor : '#ff8c00'})`
                : '',
            }}
          />
        );
      })}
    </VisualizerContainer>
  );
};

export default CircularVisualizer;
