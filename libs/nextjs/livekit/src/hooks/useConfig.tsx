'use client';

import {getCookie, setCookie} from 'cookies-next';
import {useRouter} from 'next/navigation';
import React, {createContext, type ReactNode, useCallback, useEffect, useMemo, useState,} from 'react';

type AppSettings = {
  editable: boolean;
  chat: boolean;
  inputs: {
    mic: boolean;
  };
  outputs: {
    audio: boolean;
    chat?: boolean;
  };
  ws_url: string;
  token: string;
  room_name: string;
  participant_name: string;
  theme_color?: string | null;
};

type AppConfig = {
  settings: AppSettings;
};

const defaultConfig: AppConfig = {
  settings: {
    editable: true,
    chat: true,
    inputs: {
      mic: true,
    },
    outputs: {
      audio: true,
    },
    ws_url: '',
    token: '',
    room_name: '',
    participant_name: '',
  },
};

const useAppConfig = (): AppConfig => {
  return useMemo(() => {
    try {
      const parsedConfig: Partial<AppConfig> = {
        settings: {
          editable: true,
          chat: true,
          outputs: {
            audio: true,
          },
          inputs: {
            mic: true,
          },
          ws_url: '',
          token: '',
          room_name: '',
          participant_name: '',
        },
      };
      if (parsedConfig.settings === undefined) {
        parsedConfig.settings = defaultConfig.settings;
      }
      if (parsedConfig.settings.editable === undefined) {
        parsedConfig.settings.editable = true;
      }
      return parsedConfig as AppConfig;
    } catch (e) {
      console.error('Error parsing app config:', e);
    }
    return defaultConfig;
  }, []);
};

type ConfigContextValue = {
  config: AppConfig;
  setUserSettings: (settings: AppSettings) => void;
};

const ConfigContext = createContext<ConfigContextValue | null>(null);

export const ConfigProvider = ({children}: { children: ReactNode }) => {
  const appConfig = useAppConfig();
  const router = useRouter();
  const [localColorOverride, setLocalColorOverride] = useState<string | null>(
    null,
  );
  const getSettingsFromUrl = useCallback((): AppSettings | null => {
    if (typeof window === 'undefined') {
      return null;
    }
    if (!window.location.hash) {
      return null;
    }
    const appConfigFromSettings = appConfig;
    if (appConfigFromSettings.settings.editable === false) {
      return null;
    }
    const params = new URLSearchParams(window.location.hash.replace('#', ''));
    return {
      editable: true,
      chat: params.get('chat') === '1',
      theme_color: params.get('theme_color'),
      inputs: {
        mic: params.get('mic') === '1',
      },
      outputs: {
        audio: params.get('audio') === '1',
        chat: params.get('chat') === '1',
      },
      ws_url: '',
      token: '',
      room_name: '',
      participant_name: '',
    };
  }, [appConfig]);

  const getSettingsFromCookies = useCallback((): AppSettings | null => {
    const appConfigFromSettings = appConfig;
    if (appConfigFromSettings.settings.editable === false) {
      return null;
    }
    const jsonSettings = getCookie('lk_settings');
    if (!jsonSettings || typeof jsonSettings !== 'string') {
      return null;
    }

    console.log('jsonSettings', jsonSettings);
    return JSON.parse(jsonSettings) as AppSettings;
  }, [appConfig]);

  const setUrlSettings = useCallback(
    (us: AppSettings) => {
      const obj = new URLSearchParams({
        mic: boolToString(us.inputs.mic),
        audio: boolToString(us.outputs.audio),
        chat: boolToString(us.chat),
        theme_color: us.theme_color || 'cyan',
      });
      // Note: We don't set ws_url and token to the URL on purpose
      router.replace('/#' + obj.toString());
    },
    [router],
  );

  const setCookieSettings = useCallback((us: AppSettings) => {
    const json = JSON.stringify(us);
    setCookie('lk_settings', json);
  }, []);

  const getConfig = useCallback((): AppConfig => {
    const appConfigFromSettings = appConfig;

    if (appConfigFromSettings.settings.editable === false) {
      if (localColorOverride) {
        appConfigFromSettings.settings.theme_color = localColorOverride;
      }
      return appConfigFromSettings;
    }
    const cookieSettigs = getSettingsFromCookies();
    const urlSettings = getSettingsFromUrl();
    if (!cookieSettigs) {
      if (urlSettings) {
        setCookieSettings(urlSettings);
      }
    }
    if (!urlSettings) {
      if (cookieSettigs) {
        setUrlSettings(cookieSettigs);
      }
    }
    const newCookieSettings = getSettingsFromCookies();
    if (!newCookieSettings) {
      return appConfigFromSettings;
    }
    appConfigFromSettings.settings = newCookieSettings;
    return {...appConfigFromSettings};
  }, [
    appConfig,
    getSettingsFromCookies,
    getSettingsFromUrl,
    localColorOverride,
    setCookieSettings,
    setUrlSettings,
  ]);

  const setUserSettings = useCallback(
    (settings: AppSettings) => {
      const appConfigFromSettings = appConfig;
      if (appConfigFromSettings.settings.editable === false) {
        setLocalColorOverride(settings.theme_color ?? null);
        return;
      }
      setUrlSettings(settings);
      setCookieSettings(settings);
      _setConfig((prev) => {
        return {
          ...prev,
          settings: settings,
        };
      });
    },
    [appConfig, setCookieSettings, setUrlSettings],
  );

  const [config, _setConfig] = useState<AppConfig>(getConfig());

  // Run things client side because we use cookies
  useEffect(() => {
    _setConfig(getConfig());
  }, [getConfig]);

  return (
    <ConfigContext.Provider value={{config, setUserSettings}}>
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => {
  const context = React.useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

const boolToString = (b: boolean) => (b ? '1' : '0');
