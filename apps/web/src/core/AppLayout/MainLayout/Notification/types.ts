export type NotificationItemData = {
  token?: string;
  title?: string;
  description?: string;
  body?: string;
  message?: string;
  event?: string;
  event_data?: { slug?: string; [key: string]: unknown };
  color?: string;
  object_type?: string;
  object_id?: string | number;
  created?: string;
  read?: boolean;
  expired?: boolean;
  [key: string]: unknown;
};

export type NotificationExtra = {
  unread_count?: number;
  count?: number;
  [key: string]: unknown;
};
