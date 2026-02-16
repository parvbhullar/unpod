import type { LocaleEntry } from '../types';
import deMessages from '../locales/de_DE.json';
import deDE from 'antd/lib/locale/de_DE';

const DeLang: LocaleEntry = {
  messages: {
    ...deMessages,
  },
  antLocale: deDE,
  locale: 'de-DE',
  direction: 'ltr',
};
export default DeLang;