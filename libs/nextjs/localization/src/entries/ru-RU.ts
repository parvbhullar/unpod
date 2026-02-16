import type { LocaleEntry } from '../types';
import ruMessages from '../locales/ru_RU.json';
import ruRU from 'antd/lib/locale/ru_RU';

const RuLang: LocaleEntry = {
  messages: {
    ...ruMessages,
  },
  antLocale: ruRU,
  locale: 'ru-RU',
  direction: 'ltr',
};
export default RuLang;