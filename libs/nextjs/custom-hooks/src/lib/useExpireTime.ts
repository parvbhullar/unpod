'use client';

import { Dispatch, SetStateAction, useEffect, useState } from 'react';

export type UseExpireTimeResult = {
  resetTimer: () => void;
  stopTimer: () => void;
  remainingTime: number;
  setRemainingTime: Dispatch<SetStateAction<number>>;
  minutes: string;
  seconds: string;};

let timer: ReturnType<typeof setInterval> | undefined;

export const useExpireTime = (time = 60): UseExpireTimeResult => {
  const [remainingTime, setRemainingTime] = useState<number>(time);

  useEffect(() => {
    if (time > 0) {
      timer = setInterval(() => {
        setRemainingTime((remainingTime) => remainingTime - 1);
      }, 1000);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [time]);

  useEffect(() => {
    if (remainingTime === 0 && timer) {
      clearInterval(timer);
    }
  }, [remainingTime]);

  const resetTimer = (): void => {
    setRemainingTime(time);
    timer = setInterval(() => {
      setRemainingTime((remainingTime) => remainingTime - 1);
    }, 1000);
  };

  const stopTimer = (): void => {
    if (timer) clearInterval(timer);
  };

  return {
    resetTimer,
    stopTimer,
    remainingTime,
    setRemainingTime,
    minutes: Math.trunc(remainingTime / 60).toLocaleString('en-US', {
      minimumIntegerDigits: 2,
      useGrouping: false,
    }),
    seconds: (remainingTime % 60).toLocaleString('en-US', {
      minimumIntegerDigits: 2,
      useGrouping: false,
    }),
  };
};
