import type { LocaleEntry } from '../types';
import plMessages from '../locales/pl_PL.json';
import plPL from 'antd/lib/locale/pl_PL';

const PlLang: LocaleEntry = {
  messages: {
    ...plMessages,
  },
  antLocale: plPL,
  locale: 'pl-PL',
  direction: 'ltr',
};
export default PlLang;