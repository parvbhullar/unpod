import type {LocaleEntry} from '../types';
import itMessages from '../locales/it_IT.json';
import itIT from 'antd/lib/locale/it_IT';

const ItLang: LocaleEntry = {
  messages: {
    ...itMessages,
  },
  antLocale: itIT,
  locale: 'it-IT',
  direction: 'ltr',
};
export default ItLang;
