'use client';

import React, { ReactNode, useEffect } from 'react';
import { IntlProvider, useIntl } from 'react-intl';
import { ConfigProvider } from 'antd';

import AppLocale from '@unpod/localization';
import { useAppContext } from '../context-provider';

export { useLocale } from './useLocale';

type AppLocaleEntry = {
  locale: string;
  messages: Record<string, string>;
  antLocale: unknown;
  direction?: 'ltr' | 'rtl';};

export type AppLocaleProviderProps = {
  children: ReactNode;};

export const AppLocaleProvider: React.FC<AppLocaleProviderProps> = ({
  children,
}) => {
  const { locale } = useAppContext();
  const currentAppLocale = (AppLocale as Record<string, AppLocaleEntry>)[
    locale.locale
  ];
  const direction = currentAppLocale.direction || 'ltr';

  useEffect(() => {
    document.documentElement.dir = direction;
    document.documentElement.lang = currentAppLocale.locale;
  }, [direction, currentAppLocale.locale]);

  return (
    <IntlProvider
      locale={currentAppLocale.locale}
      messages={currentAppLocale.messages}
    >
      <ConfigProvider
        direction={direction}
        locale={currentAppLocale.antLocale as undefined}
      >
        {children}
      </ConfigProvider>
    </IntlProvider>
  );
};

export default AppLocaleProvider;

export { useIntl };
