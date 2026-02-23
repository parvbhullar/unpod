import {debounce, DebouncedFunc} from 'lodash';
import {useEffect, useMemo, useState} from 'react';

export const useDebounceValue = <T>(value: T, delay = 400): T => {
  const [currentVal, setCurrentVal] = useState<T>(value);

  const debounceFun: DebouncedFunc<(newValue: T) => void> = useMemo(
    () =>
      debounce((newValue: T) => {
        setCurrentVal(newValue);
      }, delay),
    [delay],
  );

  useEffect(() => {
    if (currentVal === value) {
      return;
    }
    debounceFun(value);
    return () => {
      debounceFun?.cancel();
    };
  }, [value, debounceFun]);

  return currentVal;
};
