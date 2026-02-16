'use client';

import React, { ReactNode } from 'react';
import { ConfigProvider, ThemeConfig } from 'antd';
import AppLocale from '@unpod/localization';
import { useAppContext } from '../context-provider';

type AppLocaleEntry = {
  antLocale: unknown;};

export type Theme = {
  font: {
    family: string;
  };
  palette: {
    primary: string;
    text: {
      primary: string;
      secondary: string;
    };
  };
  radius: {
    base: number;
    sm: number;
  };
  border: {
    color: string;
  };};

export type AppThemeProviderProps = {
  children: ReactNode;
  theme: Theme;};

export const AppThemeProvider: React.FC<AppThemeProviderProps> = ({
  theme,
  children,
}) => {
  const { locale } = useAppContext();
  const { antLocale } =
    (AppLocale as Record<string, AppLocaleEntry>)[locale.locale] ||
    (AppLocale as Record<string, AppLocaleEntry>)['en'];

  const themeSettings: ThemeConfig = {
    cssVar: { key: 'unpod' },
    token: {
      fontFamily: theme.font.family,
      colorPrimary: theme.palette.primary,
      borderRadius: theme.radius.base,
      borderRadiusSM: theme.radius.sm,
      colorLink: theme.palette.primary,
      colorTextBase: theme.palette.text.primary,
      colorSplit: theme.border.color,
      colorTextSecondary: theme.palette.text.secondary,
    },
    components: {
      Layout: {
        headerBg: '#fff',
      },
      Typography: {
        fontSizeHeading1: 36,
        fontSizeHeading2: 24,
        fontSizeHeading3: 21,
        fontSizeHeading4: 18,
        colorTextDescription: 'rgba(0, 0, 0, 0.5)',
      },
      Menu: {},
      Upload: {},
      Button: {
        controlHeight: 40,
        borderRadius: theme.radius.base,
        controlHeightSM: 32,
        controlHeightLG: 48,
      },
      List: {
        colorTextDescription: 'rgba(0, 0, 0, 0.5)',
      },
      Input: {
        colorTextPlaceholder: 'rgba(0, 0, 0, 0.35)',
      },
    },
  };

  return (
    <ConfigProvider
      csp={{ nonce: 'unpod' }}
      locale={antLocale as undefined}
      theme={themeSettings}
    >
      {children}
    </ConfigProvider>
  );
};

export default AppThemeProvider;
