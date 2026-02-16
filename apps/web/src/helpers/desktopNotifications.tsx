/**
 * Desktop Notification API for Tauri
 * Provides notification functionality for Tauri desktop app with browser fallback
 */

// Cache for Tauri invoke function
type TauriInvoke = (
  cmd: string,
  args?: Record<string, unknown>,
) => Promise<any>;
let tauriInvoke: TauriInvoke | null = null;

// Check if running in Tauri environment
const isTauri = () => {
  if (typeof window === 'undefined') return false;

  // Only return true if Tauri globals are actually present
  return '__TAURI__' in window || '__TAURI_INTERNALS__' in window;
};

/**
 * Update notification badge count
 * @param {number} count - Number of unread notifications
 */
export const updateNotificationBadge = async (count: number) => {
  console.log(
    '[desktopNotifications] updateNotificationBadge called with count:',
    count,
  );
  console.log('[desktopNotifications] Environment check:', {
    isTauri: isTauri(),
    hasTauriGlobal: typeof window !== 'undefined' && '__TAURI__' in window,
  });

  try {
    if (isTauri()) {
      // Tauri implementation
      console.log('[Tauri] Attempting to invoke update_notification_badge...');

      // Use imported invoke or dynamically import
      let invoke = tauriInvoke;
      if (!invoke) {
        try {
          const module = await import('@tauri-apps/api/core');
          invoke = module.invoke;
          tauriInvoke = invoke; // Cache for future use
        } catch (importError) {
          console.error(
            '[Tauri] Failed to import @tauri-apps/api/core:',
            importError,
          );
          // Fallback to browser behavior
          document.title = count > 0 ? `(${count}) Unpod` : 'Unpod';
          return;
        }
      }

      if (!invoke) {
        console.warn(
          '[Tauri] invoke function not available, using browser fallback',
        );
        document.title = count > 0 ? `(${count}) Unpod` : 'Unpod';
        return;
      }

      await invoke('update_notification_badge', { count });
      console.log(`[Tauri] Badge updated to ${count}`);
    } else {
      // Browser fallback - update document title
      console.log('[Browser] Updating document title...');
      document.title = count > 0 ? `(${count}) Unpod` : 'Unpod';
      console.log(`[Browser] Title updated to: ${document.title}`);
    }
  } catch (error) {
    console.error(
      '[desktopNotifications] Failed to update notification badge:',
      error,
    );
    // Fallback to browser behavior on error
    try {
      document.title = count > 0 ? `(${count}) Unpod` : 'Unpod';
    } catch {
      // Ignore title update errors
    }
  }
};

/**
 * Show a system notification
 * @param {string} title - Notification title
 * @param {string} body - Notification body
 */
export const showNotification = async (title: string, body: string) => {
  try {
    console.log('[desktopNotifications] showNotification called:', {
      title,
      body,
      isTauri: isTauri(),
    });

    if (isTauri()) {
      // Tauri implementation
      console.log('[desktopNotifications] Using Tauri notification');
      let invoke = tauriInvoke;
      if (!invoke) {
        try {
          console.log('[desktopNotifications] Importing Tauri invoke');
          const module = await import('@tauri-apps/api/core');
          invoke = module.invoke;
          tauriInvoke = invoke;
        } catch (importError) {
          console.error(
            '[Tauri] Failed to import @tauri-apps/api/core:',
            importError,
          );
          // Fallback to browser notification
          if (
            'Notification' in window &&
            Notification.permission === 'granted'
          ) {
            new Notification(title, { body });
          }
          return;
        }
      }

      if (!invoke) {
        console.warn(
          '[Tauri] invoke function not available, using browser fallback',
        );
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(title, { body });
        }
        return;
      }

      console.log(
        '[desktopNotifications] Calling Tauri show_notification command',
      );
      await invoke('show_notification', { title, body });
      console.log(
        `[desktopNotifications] Tauri notification shown successfully: ${title}`,
      );
    } else {
      // Browser fallback - use Web Notifications API
      console.log('[desktopNotifications] Using browser notification');
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body });
        console.log('[desktopNotifications] Browser notification shown');
      } else if (
        'Notification' in window &&
        Notification.permission !== 'denied'
      ) {
        const permission = await Notification.requestPermission();
        console.log('[desktopNotifications] Permission result:', permission);
        if (permission === 'granted') {
          new Notification(title, { body });
          console.log(
            '[desktopNotifications] Browser notification shown after permission',
          );
        }
      }
    }
  } catch (error) {
    console.error('[desktopNotifications] Failed to show notification:', error);
    // Try browser fallback on any error
    try {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body });
      }
    } catch {
      // Ignore notification errors
    }
  }
};

/**
 * Check notification permission
 * @returns {Promise<string>} 'granted', 'denied', or 'unknown'
 */
export const checkNotificationPermission = async (): Promise<string> => {
  try {
    if (isTauri()) {
      let invoke = tauriInvoke;
      if (!invoke) {
        const { invoke: importedInvoke } = await import('@tauri-apps/api/core');
        invoke = importedInvoke;
      }
      return await invoke('check_notification_permission');
    } else {
      // Browser
      if ('Notification' in window) {
        return Notification.permission === 'granted'
          ? 'granted'
          : Notification.permission === 'denied'
            ? 'denied'
            : 'unknown';
      }
      return 'unknown';
    }
  } catch (error) {
    console.error('Failed to check notification permission:', error);
    return 'unknown';
  }
};

/**
 * Request notification permission
 * @returns {Promise<boolean>} true if granted
 */
export const requestNotificationPermission = async (): Promise<boolean> => {
  try {
    if (isTauri()) {
      let invoke = tauriInvoke;
      if (!invoke) {
        const { invoke: importedInvoke } = await import('@tauri-apps/api/core');
        invoke = importedInvoke;
      }
      return await invoke('request_notification_permission');
    } else {
      // Browser
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
      }
      return false;
    }
  } catch (error) {
    console.error('Failed to request notification permission:', error);
    return false;
  }
};

/**
 * Get platform information
 * @returns {Promise<{platform: string, isTauri: boolean, isBrowser: boolean}>}
 */
export const getPlatformInfo = async (): Promise<{
  platform?: string;
  version?: string;
  isTauri: boolean;
  isBrowser: boolean;
}> => {
  const info: {
    platform?: string;
    version?: string;
    isTauri: boolean;
    isBrowser: boolean;
  } = {
    isTauri: isTauri(),
    isBrowser: !isTauri(),
  };

  try {
    if (isTauri()) {
      let invoke = tauriInvoke;
      if (!invoke) {
        const { invoke: importedInvoke } = await import('@tauri-apps/api/core');
        invoke = importedInvoke;
      }
      info.platform = await invoke('get_platform');
      info.version = await invoke('get_app_version');
    } else {
      info.platform = navigator.platform;
    }
  } catch (error) {
    console.error('Failed to get platform info:', error);
    info.platform = 'unknown';
  }

  return info;
};

// Export utilities
export const desktopAPI = {
  isTauri,
  isDesktop: () => isTauri(),
  updateNotificationBadge,
  showNotification,
  checkNotificationPermission,
  requestNotificationPermission,
  getPlatformInfo,
};

export default desktopAPI;
