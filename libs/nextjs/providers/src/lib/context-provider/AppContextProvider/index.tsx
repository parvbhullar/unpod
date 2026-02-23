'use client';

import type {SetStateAction} from 'react';
import React, {createContext, useCallback, useContext, useEffect, useMemo, useState,} from 'react';
import type {
  AppActionsContextType,
  AppContextProviderProps,
  AppContextState,
  LocaleConfig,
} from '@unpod/constants/types';
// Browser storage key for persisting locale preference
const LOCALE_STORAGE_KEY = 'unpod_locale';

const parseListingType = (
  value: string | null,
  fallback: 'grid' | 'list',
): 'grid' | 'list' => {
  return value === 'grid' || value === 'list' ? value : fallback;
};

const ContextState: AppContextState = {
  locale: {
    languageId: 'english',
    locale: 'en',
    name: 'English',
    icon: 'us',
  },
  themeMode: 'light',
  collapsed: false,
  listingType: 'list',
  isCallRecording: false,
};

const AppContext = createContext<AppContextState>(ContextState);
const AppActionsContext = createContext<AppActionsContextType | undefined>(
  undefined,
);

export const useAppContext = (): AppContextState => useContext(AppContext);
export const useAppActionsContext = (): AppActionsContextType => {
  const context = useContext(AppActionsContext);
  if (!context) {
    throw new Error(
      'useAppActionsContext must be used within AppContextProvider',
    );
  }
  return context;
};

// Initialize state with locale from localStorage if available
const initializeState = (defaultState: AppContextState): AppContextState => {
  // Check if we're in browser environment
  if (typeof window !== 'undefined') {
    try {
      const listType = localStorage.getItem('list_type');
      const sidebarStatus = localStorage.getItem('sidebar-status');
      const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY);
      if (savedLocale) {
        const parsedLocale = JSON.parse(savedLocale) as LocaleConfig;
        return {
          ...defaultState,
          locale: parsedLocale,
          listingType: parseListingType(listType, defaultState.listingType),
          collapsed: sidebarStatus === 'collapsed',
        };
      }
      if (listType || sidebarStatus) {
        return {
          ...defaultState,
          listingType: parseListingType(listType, defaultState.listingType),
          collapsed: sidebarStatus === 'collapsed',
        };
      }
    } catch (error) {
      console.warn('Failed to load locale from localStorage:', error);
    }
  }
  return defaultState;
};

export const AppContextProvider: React.FC<AppContextProviderProps> = ({
                                                                        children,
                                                                      }) => {
  const [state, setState] = useState<AppContextState>(() =>
    initializeState(ContextState),
  );

  const updateLocale = useCallback((locale: LocaleConfig) => {
    setState((prev: AppContextState) => ({
      ...prev,
      locale,
    }));
  }, []);

  const updateThemeMode = useCallback((mode: 'light' | 'dark' | 'system') => {
    setState((prev: AppContextState) => ({
      ...prev,
      themeMode: mode,
    }));
  }, []);

  const setCollapsed = useCallback((collapsed: boolean) => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(
          'sidebar-status',
          collapsed ? 'collapsed' : 'expanded',
        );
      } catch (error) {
        console.warn('Failed to save sidebar state to localStorage:', error);
      }
    }
    setState((prev: AppContextState) => ({
      ...prev,
      collapsed,
    }));
  }, []);

  const setListingType = useCallback(
    (value: SetStateAction<'grid' | 'list'>) => {
      setState((prev: AppContextState) => {
        const nextValue =
          typeof value === 'function' ? value(prev.listingType) : value;
        if (typeof window !== 'undefined') {
          try {
            localStorage.setItem('list_type', nextValue);
          } catch (error) {
            console.warn('Failed to save listing type to localStorage:', error);
          }
        }
        return {
          ...prev,
          listingType: nextValue,
        };
      });
    },
    [],
  );

  const setCallRecording = useCallback((value: SetStateAction<boolean>) => {
    setState((prev: AppContextState) => ({
      ...prev,
      isCallRecording:
        typeof value === 'function' ? value(prev.isCallRecording) : value,
    }));
  }, []);

  // Save locale to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(LOCALE_STORAGE_KEY, JSON.stringify(state.locale));
      } catch (error) {
        console.warn('Failed to save locale to localStorage:', error);
      }
    }
  }, [state.locale]);

  const actions = useMemo<AppActionsContextType>(
    () => ({
      updateLocale,
      updateThemeMode,
      setCollapsed,
      setListingType,
      setCallRecording,
    }),
    [
      updateLocale,
      updateThemeMode,
      setCollapsed,
      setListingType,
      setCallRecording,
    ],
  );

  return (
    <AppActionsContext.Provider value={actions}>
      <AppContext.Provider value={state}>{children}</AppContext.Provider>
    </AppActionsContext.Provider>
  );
};

export default AppContextProvider;
