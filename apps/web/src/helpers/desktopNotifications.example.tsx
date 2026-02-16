/**
 * Desktop Notifications API - Usage Examples
 * Works with Tauri and Browser
 */

import {
  checkNotificationPermission,
  desktopAPI,
  getPlatformInfo,
  requestNotificationPermission,
  showNotification,
  updateNotificationBadge,
} from './desktopNotifications';
// ============================================
// Example 5: Use in React Component
// ============================================
import { useEffect } from 'react';

// ============================================
// Example 1: Update Badge Count
// ============================================
async function updateBadgeExample() {
  // Simple usage
  await updateNotificationBadge(5); // Shows "(5) Unpod" in title/tray

  // Clear badge
  await updateNotificationBadge(0);
}

// ============================================
// Example 2: Show Notification
// ============================================
async function showNotificationExample() {
  // Show a notification
  await showNotification('New Message', 'You have a new message from John');

  // Show with dynamic content
  const userName = 'Alice';
  const messagePreview = 'Hey, are you available?';
  await showNotification(`New message from ${userName}`, messagePreview);
}

// ============================================
// Example 3: Check & Request Permission
// ============================================
async function permissionExample() {
  // Check current permission
  const permission = await checkNotificationPermission();
  console.log('Permission:', permission); // 'granted', 'denied', or 'unknown'

  // Request permission if not granted
  if (permission !== 'granted') {
    const granted = await requestNotificationPermission();
    if (granted) {
      console.log('Permission granted!');
      await showNotification(
        'Notifications Enabled',
        'You will now receive notifications',
      );
    }
  }
}

// ============================================
// Example 4: Platform Detection
// ============================================
async function platformExample() {
  const info = await getPlatformInfo();
  console.log('Platform info:', info);
  // {
  //   isTauri: true/false,
  //   isBrowser: true/false,
  //   platform: 'darwin' | 'windows' | 'linux',
  //   version: '2.0.0'
  // }

  if (info.isTauri) {
    console.log('Running in Tauri desktop app!');
  } else {
    console.log('Running in Browser');
  }
}

type NotificationComponentProps = {
  unreadCount: number;
  newMessage?: { sender: string; preview: string } | null;
};

function NotificationComponent({
  unreadCount,
  newMessage,
}: NotificationComponentProps) {
  // Update badge when count changes
  useEffect(() => {
    updateNotificationBadge(unreadCount);
  }, [unreadCount]);

  // Show notification when new message arrives
  useEffect(() => {
    if (newMessage) {
      showNotification(
        `New message from ${newMessage.sender}`,
        newMessage.preview,
      );
    }
  }, [newMessage]);

  return <div>Notifications: {unreadCount}</div>;
}

// ============================================
// Example 6: Conditional Desktop Features
// ============================================
async function conditionalFeatures() {
  if (desktopAPI.isDesktop()) {
    // Desktop-only features
    await updateNotificationBadge(3);
    await showNotification('Desktop App', 'Running in desktop mode');

    // Get platform-specific info
    const info = await getPlatformInfo();
    if (info.platform === 'darwin') {
      console.log('Running on macOS');
    }
  } else {
    // Browser fallback
    document.title = '(3) Unpod';
    console.log('Running in browser');
  }
}

// ============================================
// Example 7: Error Handling
// ============================================
async function errorHandlingExample() {
  try {
    await showNotification('Test', 'Testing notification');
    console.log('Notification sent successfully');
  } catch (error) {
    console.error('Failed to send notification:', error);
    // Fallback to browser notification or UI alert
  }
}

// ============================================
// Example 8: Integration with Message System
// ============================================
async function messageSystemExample(
  messages: Array<{ read?: boolean; preview?: string }>,
) {
  const unreadMessages = messages.filter((m) => !m.read);
  const unreadCount = unreadMessages.length;

  // Update badge
  await updateNotificationBadge(unreadCount);

  // Show notification for latest message
  if (unreadMessages.length > 0) {
    const latest = unreadMessages[0];
    await showNotification(
      `${unreadMessages.length} new messages`,
      `Latest: ${latest.preview}`,
    );
  }
}

// Export examples for testing
export const examples = {
  updateBadgeExample,
  showNotificationExample,
  permissionExample,
  platformExample,
  conditionalFeatures,
  errorHandlingExample,
  messageSystemExample,
  NotificationComponent,
};
