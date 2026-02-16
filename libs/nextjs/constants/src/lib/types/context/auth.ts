import type { ReactNode } from 'react';
import type { Organization } from '../organization';
import type { User } from '../user';

export type GlobalData = {
  permissions: unknown | null;
  roles: unknown | null;
  profile_roles: unknown | null;
};

export type Subscription = {
  [key: string]: unknown;
};

export type AuthState = {
  user: User | null;
  activeOrg: Organization | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  visitorId: string | null;
  subscription: Subscription | null;
  currency: string | undefined;
  globalData: GlobalData;
};

export type AuthAction = {
  type:
    | 'SET_AUTH_USER'
    | 'UPDATE_AUTH_USER'
    | 'UPDATE_AUTH_LOADING'
    | 'UPDATE_ACTIVE_ORGANIZATION'
    | 'LOGOUT_AUTH_USER'
    | 'SET_VISITOR_ID'
    | 'UPDATE_SUBSCRIPTION'
    | 'UPDATE_GLOBAL_DATA';
  payload?: unknown;
};

export type AuthActionsContextType = {
  onSuccessAuthenticate: (user: User) => void;
  storeToken: (token: string) => Promise<unknown>;
  setActiveOrg: (org: Organization | null) => void;
  getSubscription: () => void;
  getAuthUser: () => Promise<unknown>;
  updateAuthUser: (user: User | null) => void;
  signInUser: (payload: unknown) => Promise<unknown>;
  signUpUser: (payload: unknown) => Promise<unknown>;
  logoutUser: () => Promise<unknown>;
  getGlobalData: () => Promise<unknown>;
};

export type AuthContextProviderProps = {
  children: ReactNode;
  userData?: {
    user?: User;
    token?: string;
  };
  isAuthenticate?: boolean;
};
