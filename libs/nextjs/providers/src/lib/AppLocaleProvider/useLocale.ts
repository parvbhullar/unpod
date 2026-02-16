'use client';

import { IntlShape, useIntl } from 'react-intl';
import { useAppActionsContext, useAppContext } from '../context-provider';
import AppLocale from '@unpod/localization';
import type { LocaleConfig } from '@unpod/constants/types';

export type UseLocaleResult = {
  locale: string;
  languageId: string;
  languageName: string;
  direction: 'ltr' | 'rtl';
  isRTL: boolean;
  formatMessage: IntlShape['formatMessage'];
  formatNumber: IntlShape['formatNumber'];
  formatDate: IntlShape['formatDate'];
  formatTime: IntlShape['formatTime'];
  changeLocale: (locale: LocaleConfig) => void;
  intl: IntlShape;
};

/**
 * Custom hook for accessing localization utilities
 * @returns Localization utilities
 */
export const useLocale = (): UseLocaleResult => {
  const intl = useIntl();
  const { locale } = useAppContext();
  const { updateLocale } = useAppActionsContext();
  const currentAppLocale = (
    AppLocale as Record<string, { direction?: 'ltr' | 'rtl' }>
  )[locale.locale];

  return {
    // Current locale info
    locale: locale.locale,
    languageId: locale.languageId,
    languageName: locale.name,
    direction: currentAppLocale?.direction || 'ltr',
    isRTL: currentAppLocale?.direction === 'rtl',

    // Intl methods
    formatMessage: intl.formatMessage,
    formatNumber: intl.formatNumber,
    formatDate: intl.formatDate,
    formatTime: intl.formatTime,

    // Actions
    changeLocale: updateLocale,

    // Full intl object for advanced usage
    intl,
  };
};

export default useLocale;
