/**
 * Tauri API Bridge
 * This file provides a bridge between the Next.js app and Tauri backend
 * Compatible with Electron IPC interface for easy migration
 */

import { invoke } from '@tauri-apps/api/core';

// ============================================
// Session Management
// ============================================

export const tauriApi = {
  // Session token management
  sessionGetToken: async (): Promise<string | null> => {
    return await invoke('session_get_token');
  },

  sessionSetToken: async (token: string): Promise<boolean> => {
    return await invoke('session_set_token', { token });
  },

  sessionDeleteToken: async (): Promise<boolean> => {
    return await invoke('session_delete_token');
  },

  // Generic session storage
  sessionGet: async (key: string): Promise<string | null> => {
    return await invoke('session_get', { key });
  },

  sessionSet: async (key: string, value: string): Promise<boolean> => {
    return await invoke('session_set', { key, value });
  },

  sessionDelete: async (key: string): Promise<boolean> => {
    return await invoke('session_delete', { key });
  },

  sessionClear: async (): Promise<boolean> => {
    return await invoke('session_clear');
  },

  // ============================================
  // System Information
  // ============================================

  getPlatform: async (): Promise<string> => {
    return await invoke('get_platform');
  },

  getTheme: async (): Promise<'light' | 'dark'> => {
    return await invoke('get_theme');
  },

  getAppVersion: async (): Promise<string> => {
    return await invoke('get_app_version');
  },

  // ============================================
  // Window Controls
  // ============================================

  windowMinimize: async (): Promise<void> => {
    return await invoke('window_minimize');
  },

  windowMaximize: async (): Promise<void> => {
    return await invoke('window_maximize');
  },

  windowClose: async (): Promise<void> => {
    return await invoke('window_close');
  },

  openExternal: async (url: string): Promise<void> => {
    return await invoke('open_external', { url });
  },

  // ============================================
  // Notifications
  // ============================================

  checkNotificationPermission: async (): Promise<
    'granted' | 'denied' | 'unknown'
  > => {
    return await invoke('check_notification_permission');
  },

  requestNotificationPermission: async (): Promise<boolean> => {
    return await invoke('request_notification_permission');
  },

  showNotification: async (title: string, body: string): Promise<void> => {
    return await invoke('show_notification', { title, body });
  },

  updateNotificationBadge: async (count: number): Promise<void> => {
    return await invoke('update_notification_badge', { count });
  },

  // ============================================
  // Auto-Updater
  // ============================================

  updaterCheckForUpdates: async (): Promise<string> => {
    return await invoke('updater_check_for_updates');
  },

  updaterDownloadAndInstall: async (): Promise<void> => {
    return await invoke('updater_download_and_install');
  },
};

// Check if running in Tauri environment
export const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

// Export a unified API that works in both environments
export default tauriApi;
