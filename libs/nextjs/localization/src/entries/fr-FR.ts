import type { LocaleEntry } from '../types';
import frMessages from '../locales/fr_FR.json';
import frFR from 'antd/lib/locale/fr_FR';

const FrLang: LocaleEntry = {
  messages: {
    ...frMessages,
  },
  antLocale: frFR,
  locale: 'fr-FR',
  direction: 'ltr',
};
export default FrLang;