import type {LocaleEntry} from '../types';
import nlMessages from '../locales/nl_NL.json';
import nlNL from 'antd/lib/locale/nl_NL';

const NlLang: LocaleEntry = {
  messages: {
    ...nlMessages,
  },
  antLocale: nlNL,
  locale: 'nl-NL',
  direction: 'ltr',
};
export default NlLang;
