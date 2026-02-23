import type {LocaleEntry} from '../types';
import guMessages from '../locales/gu_IN.json';
import enUS from 'antd/lib/locale/en_US';

const GuLang: LocaleEntry = {
  messages: {
    ...guMessages,
  },
  antLocale: enUS, // Ant Design doesn't have Gujarati locale, using English as fallback
  locale: 'gu-IN',
  direction: 'ltr',
};
export default GuLang;
