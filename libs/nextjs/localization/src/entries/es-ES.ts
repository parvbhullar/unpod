import type { LocaleEntry } from '../types';
import esMessages from '../locales/es_ES.json';
import esES from 'antd/lib/locale/es_ES';

const EsLang: LocaleEntry = {
  messages: {
    ...esMessages,
  },
  antLocale: esES,
  locale: 'es-ES',
  direction: 'ltr',
};
export default EsLang;