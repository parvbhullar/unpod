import {useCallback, useEffect, useState} from 'react';
import screenfull from 'screenfull';
import {message} from 'antd';

export const useFullscreen = () => {
  const [isFullScreenEnabled, setIsFullScreenEnabled] = useState(
    screenfull.isFullscreen
  );

  const toggle = useCallback(async () => {
    if (!screenfull.isEnabled) {
      message.error('Fullscreen feature not supported');
      return;
    }
    try {
      if (isFullScreenEnabled) {
        await screenfull.exit();
      } else {
        await screenfull.request();
      }
    } catch (err) {
      message.error(err.message);
    }
  }, [isFullScreenEnabled]);

  useEffect(() => {
    const onChange = () => {
      setIsFullScreenEnabled(screenfull.isFullscreen);
    };
    if (screenfull.isEnabled) {
      screenfull.on('change', onChange);
    }
    return () => {
      if (screenfull.isEnabled) {
        screenfull.off('change', onChange);
      }
    };
  }, []);

  return {
    allowed: screenfull.isEnabled,
    isFullscreen: isFullScreenEnabled,
    toggleFullscreen: toggle,
  };
};
