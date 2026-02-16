import { useEffect, useRef, useState } from 'react';

export const generateConnectingSequenceBar = (columns) => {
  const seq = [];

  for (let x = 0; x < columns; x++) {
    seq.push([x, columns - 1 - x]);
  }

  return seq;
};
export const generateListeningSequenceBar = (columns) => {
  const center = Math.floor(columns / 2);
  const noIndex = -1;

  return [[center], [noIndex]];
};


export const useBarAnimator = (
  state,
  columns,
  interval
) => {
  const [index, setIndex] = useState(0);
  const [sequence, setSequence] = useState([[]]);

  useEffect(() => {
    if (state === 'thinking') {
      setSequence(generateListeningSequenceBar(columns));
    } else if (state === 'connecting' || state === 'initializing') {
      const sequence = [...generateConnectingSequenceBar(columns)];
      setSequence(sequence);
    } else if (state === 'listening') {
      setSequence(generateListeningSequenceBar(columns));
    } else if (state === undefined) {
      setSequence([new Array(columns).fill(0).map((_, idx) => idx)]);
    } else {
      setSequence([[]]);
    }
    setIndex(0);
  }, [state, columns]);

  const animationFrameId = useRef(null);
  useEffect(() => {
    let startTime = performance.now();

    const animate = (time) => {
      const timeElapsed = time - startTime;

      if (timeElapsed >= interval) {
        setIndex((prev) => prev + 1);
        startTime = time;
      }

      animationFrameId.current = requestAnimationFrame(animate);
    };

    animationFrameId.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameId.current !== null) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [interval, columns, state, sequence.length]);

  return sequence[index % sequence.length];
};
