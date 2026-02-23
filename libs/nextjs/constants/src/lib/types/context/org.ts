import type {Dispatch, ReactNode, SetStateAction} from 'react';

import type {NotificationData} from './app';
import type {Spaces} from '../space';

export type OrgContextType = {
  activeSpace: Spaces;
  orgUsers: OrgUser[];
  notificationData: NotificationData;
};

export type OrgActionsContextType = {
  setActiveSpace: Dispatch<SetStateAction<Spaces>>;
  setNotificationData: Dispatch<SetStateAction<NotificationData>>;
};

export type OrgUser = {
  user_email: string;
  full_name?: string;
  [key: string]: unknown;
};

export type AppOrgContextProviderProps = {
  children: ReactNode;
};
