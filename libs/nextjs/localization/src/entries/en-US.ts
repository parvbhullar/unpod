import type { LocaleEntry } from '../types';
import enMessages from '../locales/en_US.json';
import enUS from 'antd/lib/locale/en_US';

const EnLang: LocaleEntry = {
  messages: {
    ...enMessages,
  },
  antLocale: enUS,
  locale: 'en-US',
  direction: 'ltr',
};
export default EnLang;