import type {Dispatch, ReactNode, SetStateAction} from 'react';

export type LocaleConfig = {
  languageId: string;
  locale: string;
  name: string;
  icon: string;
};

export type AppContextState = {
  locale: LocaleConfig;
  themeMode: 'light' | 'dark' | 'system';
  collapsed: boolean;
  listingType: 'grid' | 'list';
  isCallRecording: boolean;
};

export type AppActionsContextType = {
  updateLocale: (locale: LocaleConfig) => void;
  updateThemeMode: (mode: 'light' | 'dark' | 'system') => void;
  setCollapsed: (state: boolean) => void;
  setListingType: Dispatch<SetStateAction<'grid' | 'list'>>;
  setCallRecording: Dispatch<SetStateAction<boolean>>;
};

export type NotificationData = {
  object_type?: string;
  event_data?: {
    domain_handle?: string;
    slug?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

export type AppContextProviderProps = {
  children: ReactNode;
};
