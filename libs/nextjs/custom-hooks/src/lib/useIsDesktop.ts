'use client';

import {useSyncExternalStore} from 'react';

type TauriWindow = Window & {
  __TAURI__?: unknown;
  __TAURI_INTERNALS__?: unknown;
};

/**
 * Check if running in desktop app environment (Tauri)
 * This runs synchronously and works during SSR
 */
const getIsDesktopApp = (): boolean => {
  if (typeof window === 'undefined') return false;
  const tauriWindow = window as TauriWindow;

  // Check for Tauri
  return (
    '__TAURI__' in tauriWindow ||
    '__TAURI_INTERNALS__' in tauriWindow ||
    tauriWindow.location.pathname.startsWith('/desktop')
  );
};

// Server snapshot always returns false (SSR)
const getServerSnapshot = (): boolean => false;

// Subscribe is a no-op since the desktop environment doesn't change
// eslint-disable-next-line @typescript-eslint/no-empty-function
const subscribe = (): (() => void) => () => {
};

export type UseIsDesktopResult = {
  isDesktopApp: boolean;
};

/**
 * Hook to detect if the app is running inside a desktop app (Tauri)
 * @returns { isDesktopApp: boolean } - true if running in Tauri
 */
export const useIsDesktop = (): UseIsDesktopResult => {
  // useSyncExternalStore ensures no hydration mismatch
  const isDesktopApp = useSyncExternalStore(
    subscribe,
    getIsDesktopApp,
    getServerSnapshot,
  );

  return {
    isDesktopApp,
  };
};

export default useIsDesktop;
