const isBrowser = typeof window !== 'undefined';

const requestAnimFrame = (callback: FrameRequestCallback): number => {
  if (isBrowser && window.requestAnimationFrame) {
    return window.requestAnimationFrame(callback);
  }
  return setTimeout(() => callback(Date.now()), 1000 / 60) as unknown as number;
};

const cancelAnimFrame = (handle: number) => {
  if (isBrowser && window.cancelAnimationFrame) {
    window.cancelAnimationFrame(handle);
  } else {
    clearTimeout(handle);
  }
};

/**
 * Behaves the same as setTimeout except uses requestAnimationFrame() where possible for better performance
 * @param {function} fn The callback function
 * @param {int} delay The delay in milliseconds
 */
type RequestTimeoutHandle = {
  value: number;};

export const requestTimeout = function (fn: () => void, delay: number) {
  if (!isBrowser || !window.requestAnimationFrame) {
    return setTimeout(fn, delay);
  }

  const start = new Date().getTime();

  const handle: RequestTimeoutHandle = { value: 0 };

  function loop() {
    const current = new Date().getTime();

    const delta = current - start;

    if (delta >= delay) {
      fn.call(null);
    } else {
      handle.value = requestAnimFrame(loop);
    }
  }

  handle.value = requestAnimFrame(loop);
  return handle;
};

/**
 * Behaves the same as clearTimeout except uses cancelRequestAnimationFrame() where possible for better performance
 * @param {int|object} fn The callback function
 */
export const clearRequestTimeout = function (
  handle: RequestTimeoutHandle | number,
) {
  if (typeof handle === 'number') {
    cancelAnimFrame(handle);
    return;
  }
  cancelAnimFrame(handle.value);
};
