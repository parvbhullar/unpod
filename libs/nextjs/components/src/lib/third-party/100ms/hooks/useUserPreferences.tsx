import {useState} from 'react';

export const UserPreferencesKeys = {
  PREVIEW: 'preview',
  NOTIFICATIONS: 'notifications',
  UI_SETTINGS: 'uiSettings',
  RTMP_URLS: 'rtmpUrls',
};

export const defaultPreviewPreference = {
  name: '',
  isAudioMuted: false,
  isVideoMuted: false,
};

export const useUserPreferences = (key, defaultPreference) => {
  const localStorageValue = localStorage.getItem(key) || defaultPreference;
  const [preference, setPreference] = useState(localStorageValue);
  const changePreference = (value) => {
    setPreference(value);
    localStorage.setItem(key, value);
  };
  return [preference, changePreference];
};
