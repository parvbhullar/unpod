import type {Locale} from 'antd/lib/locale';

export type Direction = 'ltr' | 'rtl';

export type LocaleEntry = {
  messages: Record<string, string>;
  antLocale: Locale;
  locale: string;
  direction: Direction;
};

export type LanguageData = {
  languageId: string;
  locale: string;
  name: string;
  icon: string;
  direction: Direction;
};
