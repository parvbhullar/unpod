import type {ReactNode} from 'react';

export type InfoViewState = {
  loading: boolean;
  error: string;
  notification: string;
};

export type InfoViewAction = {
  type:
    | 'FETCH_STARTS'
    | 'FETCH_SUCCESS'
    | 'SET_NOTIFICATION'
    | 'SET_ERROR'
    | 'CLEAR_ALL';
  payload?: string;
};

export type InfoViewActionsContextType = {
  fetchStart: () => void;
  fetchFinish: () => void;
  showError: (error: string) => void;
  showMessage: (notification: string) => void;
  clearAll: () => void;
};

export type AppInfoViewProviderProps = {
  children: ReactNode;
};
