'use client';

import React, {
  createContext,
  useCallback,
  useContext,
  useReducer,
} from 'react';
import type {
  AppInfoViewProviderProps,
  InfoViewActionsContextType,
  InfoViewState,
} from '@unpod/constants/types';
import {
  contextReducer,
  InfoViewActions,
} from './NotificationReducer';

const ContextState: InfoViewState = {
  loading: false,
  error: '',
  notification: '',
};

const AppInfoViewContext = createContext<InfoViewState>(ContextState);
const AppInfoViewActionsContext = createContext<
  InfoViewActionsContextType | undefined
>(undefined);

export const useInfoViewContext = (): InfoViewState =>
  useContext(AppInfoViewContext);
export const useInfoViewActionsContext = (): InfoViewActionsContextType => {
  const context = useContext(AppInfoViewActionsContext);
  if (!context) {
    throw new Error(
      'useInfoViewActionsContext must be used within AppInfoViewProvider',
    );
  }
  return context;
};

export const AppInfoViewProvider: React.FC<AppInfoViewProviderProps> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(
    contextReducer,
    ContextState,
    () => ContextState,
  );

  const fetchStart = useCallback(() => {
    dispatch({ type: InfoViewActions.FETCH_STARTS });
  }, []);

  const fetchFinish = useCallback(() => {
    dispatch({ type: InfoViewActions.FETCH_SUCCESS });
  }, []);

  const showError = useCallback((error: string) => {
    dispatch({ type: InfoViewActions.SET_ERROR, payload: error });
  }, []);

  const showMessage = useCallback((notification: string) => {
    dispatch({
      type: InfoViewActions.SET_NOTIFICATION,
      payload: notification,
    });
  }, []);

  const clearAll = useCallback(() => {
    dispatch({ type: InfoViewActions.CLEAR_ALL });
  }, []);

  const infoViewActionsContext = React.useMemo<InfoViewActionsContextType>(
    () => ({
      fetchStart,
      fetchFinish,
      showError,
      showMessage,
      clearAll,
    }),
    [fetchStart, fetchFinish, showError, showMessage, clearAll],
  );

  return (
    <AppInfoViewActionsContext.Provider value={infoViewActionsContext}>
      <AppInfoViewContext.Provider value={state}>
        {children}
      </AppInfoViewContext.Provider>
    </AppInfoViewActionsContext.Provider>
  );
};

export default AppInfoViewProvider;
