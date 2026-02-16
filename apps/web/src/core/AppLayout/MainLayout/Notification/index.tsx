'use client';

import type { NotificationExtra, NotificationItemData } from './types';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useIntl } from 'react-intl';
import { Badge, Flex, Tooltip } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { MdNotificationsNone } from 'react-icons/md';
import { IoCloseSharp } from 'react-icons/io5';

import {
  putDataApi,
  useInfoViewActionsContext,
  useOrgActionContext,
  usePaginatedDataApi,
} from '@unpod/providers';
import { httpClient } from '@unpod/services';
import { AppDrawer } from '@unpod/components/antd';
import AppList from '@unpod/components/common/AppList';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';

import { StyledMiniAvatar } from '@/core/AppLayout/MainLayout/LayoutSidebar/index.styled';
import NotificationItem from '@/core/AppLayout/MainLayout/Notification/NotificationItem';
import {
  showNotification,
  updateNotificationBadge,
} from '@/helpers/desktopNotifications';
import { disconnectCentrifugo, initCentrifugo } from '@/helpers/centrifugo';

const Notification = () => {
  const infoViewContext = useInfoViewActionsContext();
  const { setNotificationData } = useOrgActionContext();
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectAttemptsRef = useRef<number[]>([]);
  const [realTimeConnected, setRealTimeConnected] = useState(false);
  const [useCentrifugo, setUseCentrifugo] = useState(false);
  const [visible, setVisible] = useState(false);
  const { formatMessage } = useIntl();

  const [
    { apiData, loading, extraData, isLoadingMore, hasMoreRecord, page },
    { setLoadingMore, setPage, setData, setExtraData, reCallAPI },
  ] = usePaginatedDataApi<NotificationItemData[]>(
    'notifications/',
    [],
    {},
    true,
  );
  const typedExtraData = extraData as NotificationExtra;

  // Update desktop app badge count when notification count changes
  useEffect(() => {
    const unreadCount = typedExtraData?.unread_count || 0;
    console.log('[Notification] Updating badge count to:', unreadCount);
    updateNotificationBadge(unreadCount)
      .then(() => {
        console.log(
          '[Notification] Badge count updated successfully to:',
          unreadCount,
        );
      })
      .catch((error) => {
        console.error(
          '[Notification] Failed to update notification badge:',
          error,
        );
      });
  }, [typedExtraData?.unread_count]);

  // Handle incoming notification (works for both Centrifugo and SSE)
  const handleNotification = useCallback(
    (data: unknown) => {
      if (!data || typeof data !== 'object') return;
      const parsedData = data as NotificationItemData;

      console.log('[Notification] Received:', parsedData);
      setNotificationData(parsedData);

      // Show system notification
      const notificationTitle = parsedData.title || 'New Notification';
      const notificationBody =
        parsedData.message || parsedData.body || 'You have a new notification';

      showNotification(notificationTitle, notificationBody).catch((error) => {
        console.error('Failed to show notification:', error);
      });

      // Update notifications state with new notification
      setData((prevData = []) => [parsedData, ...prevData]);
      setExtraData((prevExtra) => ({
        ...(prevExtra || {}),
        unread_count:
          ((prevExtra as NotificationExtra | null)?.unread_count || 0) + 1,
        count: ((prevExtra as NotificationExtra | null)?.count || 0) + 1,
      }));
    },
    [setNotificationData, setData, setExtraData],
  );

  // Initialize real-time connection (Centrifugo with SSE fallback)
  const initRealTimeConnection = useCallback(async () => {
    if (realTimeConnected) return;

    console.log('[Notification] Initializing real-time connection...');

    // Try Centrifugo first
    const { connected, useCentrifugo: useCentrifugoResult } =
      (await initCentrifugo({
        onNotification: handleNotification,
        onConnect: () => {
          console.log('[Notification] Centrifugo connected');
          setRealTimeConnected(true);
        },
        onDisconnect: () => {
          console.log('[Notification] Centrifugo disconnected');
          setRealTimeConnected(false);
        },
        onError: (error: unknown) => {
          console.error('[Notification] Centrifugo error:', error);
        },
      })) as { connected?: boolean; useCentrifugo?: boolean };

    if (connected && useCentrifugoResult) {
      setUseCentrifugo(true);
      setRealTimeConnected(true);
      console.log('[Notification] Using Centrifugo for real-time');
      return;
    }

    // Fallback to SSE
    console.log('[Notification] Falling back to SSE...');
    setUseCentrifugo(false);
    connectSSE();
  }, [realTimeConnected, handleNotification]);

  // SSE connection fallback using httpClient
  const connectSSE = useCallback(async () => {
    if (realTimeConnected && !useCentrifugo) return;

    // Abort any existing connection
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    console.log('[Notification] Connecting to SSE stream...');
    setRealTimeConnected(true);

    let buffer = '';
    let shouldReconnect = true;

    try {
      await httpClient.get('notifications/stream/', {
        signal: abortControllerRef.current.signal,
        responseType: 'text',
        onDownloadProgress: (progressEvent: { event?: ProgressEvent }) => {
          const responseText =
            (progressEvent.event?.target as XMLHttpRequest | undefined)
              ?.responseText || '';
          const newData = responseText.slice(buffer.length);
          buffer = responseText;
          let eventName = null;

          if (newData) {
            console.log('[SSE] Chunk received:', newData);
            const lines = newData.split('\n');
            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventName = line.slice(6).trim();
                continue;
              }

              if (line.startsWith('data:') && eventName === 'notification') {
                const data = line.slice(5).trim();
                if (data) {
                  try {
                    const parsedData = JSON.parse(data);
                    handleNotification(parsedData);
                  } catch (parseError) {
                    console.warn(
                      '[SSE] Failed to parse data:',
                      data,
                      parseError,
                    );
                  }
                }
              }
            }
          }
        },
      });

      console.log('[SSE] Stream ended, will reconnect...');
    } catch (error: unknown) {
      const err = error as { name?: string; code?: string; message?: string };
      if (
        err.name === 'AbortError' ||
        err.code === 'ERR_CANCELED' ||
        err.code === 'ECONNABORTED'
      ) {
        console.log('[SSE] Connection aborted');
        shouldReconnect = false;
      } else if (err.name === 'ERR_NETWORK' || err.code === 'ERR_NETWORK') {
        console.log('[SSE] Network error, will attempt to reconnect...');
      } else {
        console.error('[SSE] Connection error:', err);
      }
    } finally {
      setRealTimeConnected(false);

      // Auto-reconnect after disconnect (unless intentionally aborted)
      if (shouldReconnect) {
        const now = Date.now();
        const fourMinutesAgo = now - 4 * 60 * 1000;

        // Filter attempts within the last 4 minutes
        reconnectAttemptsRef.current = reconnectAttemptsRef.current.filter(
          (timestamp) => timestamp > fourMinutesAgo,
        );

        if (reconnectAttemptsRef.current.length >= 3) {
          console.log(
            '[SSE] Max reconnect attempts (3) reached within 4 minutes, stopping',
          );
        } else {
          reconnectAttemptsRef.current.push(now);

          setTimeout(() => {
            console.log(
              `[SSE] Attempting reconnection (${reconnectAttemptsRef.current.length}/3)...`,
            );
            connectSSE();
          }, 3000);
        }
      }
    }
  }, [realTimeConnected, useCentrifugo, handleNotification]);

  // Initialize real-time connection on mount
  useEffect(() => {
    initRealTimeConnection();

    return () => {
      // Cleanup on unmount
      if (useCentrifugo) {
        disconnectCentrifugo();
      }
      abortControllerRef.current?.abort();
    };
  }, []);

  const updateItem = (token: string) => {
    console.log('Updating notification item with ID:', { token, apiData });
    setData((prevData = []) =>
      prevData.map((data) => {
        return data.token === token
          ? { ...data, read: true, expired: true }
          : data;
      }),
    );
    setExtraData({
      ...typedExtraData,
      unread_count:
        (typedExtraData?.unread_count || 0) > 0
          ? (typedExtraData?.unread_count || 0) - 1
          : 0,
    });
  };

  const onVisibleChange = () => {
    if (!visible && !realTimeConnected) {
      initRealTimeConnection();
    }
    if (!visible) {
      reCallAPI();
    }
    setVisible(!visible);
  };

  const readAll = () => {
    (
      putDataApi('notifications/', infoViewContext, {
        read_all: true,
      }) as Promise<unknown>
    ).then(() => {
      setData((prevData = []) =>
        prevData.map((data) => {
          return { ...data, read: true };
        }),
      );
      setExtraData({
        ...typedExtraData,
        unread_count: 0,
      });
    });
  };

  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  return (
    <>
      <Badge
        count={typedExtraData?.unread_count || 0}
        offset={[-8, 5]}
        onClick={onVisibleChange}
        data-tour="notifications"
      >
        <Tooltip
          placement="top"
          title={formatMessage({ id: 'common.notifications' })}
        >
          <StyledMiniAvatar
            icon={<MdNotificationsNone fontSize={22} />}
            className="notification-bell"
          />
        </Tooltip>
      </Badge>
      <AppDrawer
        closable={false}
        size={450}
        isTabDrawer
        title={
          <div style={{ fontSize: 18, cursor: 'pointer' }}>
            {formatMessage({ id: 'common.notifications' })}
          </div>
        }
        extra={
          <Flex align="center" gap={10}>
            <Tooltip title={formatMessage({ id: 'common.readAll' })}>
              <EyeOutlined
                style={{ fontSize: 20, cursor: 'pointer', color: '#182A88' }}
                onClick={(event) => {
                  event.preventDefault();
                  readAll();
                }}
              />
            </Tooltip>

            <AppHeaderButton
              type="text"
              shape="circle"
              onClick={() => setVisible(false)}
              icon={<IoCloseSharp size={20} />}
            />
          </Flex>
        }
        open={visible}
        onClose={onVisibleChange}
      >
        <AppList
          style={{
            height: `calc(100vh - 87px)`,
            padding: '0 10px 0 2px',
          }}
          data={apiData}
          loading={loading}
          footerProps={{
            loading: isLoadingMore,
            showCount: typedExtraData?.count,
            hasMoreRecord: hasMoreRecord,
          }}
          onEndReached={onEndReached}
          renderItem={(item) => (
            <NotificationItem
              key={item.token}
              item={item}
              loading={loading}
              updateItem={updateItem}
            />
          )}
        />
      </AppDrawer>
    </>
  );
};

export default Notification;
