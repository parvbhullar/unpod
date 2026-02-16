import type { LocaleEntry } from '../types';
import paMessages from '../locales/pa_IN.json';
import enUS from 'antd/lib/locale/en_US';

const PaLang: LocaleEntry = {
  messages: {
    ...paMessages,
  },
  antLocale: enUS, // Ant Design doesn't have Punjabi locale, using English as fallback
  locale: 'pa-IN',
  direction: 'ltr',
};
export default PaLang;