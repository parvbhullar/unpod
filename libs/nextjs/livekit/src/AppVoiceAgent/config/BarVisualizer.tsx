import React, { forwardRef, ReactNode } from 'react';
import styled, { css } from 'styled-components';
import {
  TrackReferenceOrPlaceholder,
  useMaybeTrackRefContext,
  useMultibandTrackVolume,
} from '@livekit/components-react';
import { useBarAnimator } from './useBarAnimator';

const Container = styled.div`
  display: flex;
  align-items: center;
  gap: 2px;
  height: 100%;
`;

const Bar = styled.span.withConfig({
  shouldForwardProp: (prop) =>
    prop !== 'highlighted' && prop !== 'height' && prop !== 'theme',
})<{ highlighted?: boolean; height?: number }>`
  width: 4px;
  background-color: ${({ highlighted, theme }) =>
    highlighted ? theme?.palette.secondary : '#6b7280'};
  border-radius: 2px;
  transition:
    height 0.2s ease,
    background-color 0.3s ease;
  ${({ height }) => css`
    height: ${height}%;
  `}
`;

const getSequencerInterval = (state: string | undefined, barCount: number) => {
  const sequencerIntervals = new Map([
    ['connecting', 2000],
    ['initializing', 2000],
    ['listening', 500],
    ['thinking', 150],
  ]);
  if (!state) return 1000;
  let interval = sequencerIntervals.get(state) ?? 1000;
  if (state === 'connecting') interval /= barCount;
  return interval;
};

const cloneSingleChild = (
  children: ReactNode,
  props: Record<string, unknown>,
  key: number,
) => {
  return React.Children.map(children, (child) => {
    if (React.isValidElement(child) && React.Children.only(children)) {
      return React.cloneElement(child, { ...props, key });
    }
    return child;
  });
};

type BarVisualizerOptions = {
  minHeight?: number;
  maxHeight?: number;};

type BarVisualizerProps = React.HTMLAttributes<HTMLDivElement> & {
  state?: string;
  options?: BarVisualizerOptions;
  barCount?: number;
  trackRef?: TrackReferenceOrPlaceholder;
  children?: ReactNode;};

export const BarVisualizer = forwardRef<HTMLDivElement, BarVisualizerProps>(
  ({ state, options, barCount = 15, trackRef, children, ...props }, ref) => {
    let trackReference: TrackReferenceOrPlaceholder | undefined =
      useMaybeTrackRefContext();

    if (trackRef) {
      trackReference = trackRef;
    }
    const volumeBands = useMultibandTrackVolume(trackReference, {
      bands: barCount,
      loPass: 100,
      hiPass: 200,
    }) as number[];

    const minHeight = options?.minHeight ?? 20;
    const maxHeight = options?.maxHeight ?? 100;
    const highlightedIndices = useBarAnimator(
      state,
      barCount,
      getSequencerInterval(state, barCount),
    );

    return (
      <Container ref={ref} {...props} data-lk-va-state={state}>
        {volumeBands.map((volume, idx) => {
          const height = Math.min(
            maxHeight,
            Math.max(minHeight, volume * 100 + 5),
          );
          const highlighted = highlightedIndices.includes(idx);

          if (children) {
            return cloneSingleChild(
              children,
              {
                'data-lk-highlighted': highlighted,
                'data-lk-bar-index': idx,
                style: { height: `${height}%` },
              },
              idx,
            );
          }

          return (
            <Bar
              key={idx}
              height={height}
              highlighted={!!highlighted}
              data-lk-highlighted={highlighted}
              data-lk-bar-index={idx}
            />
          );
        })}
      </Container>
    );
  },
);

BarVisualizer.displayName = 'BarVisualizer';
