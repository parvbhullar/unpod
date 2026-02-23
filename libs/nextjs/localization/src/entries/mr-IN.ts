import type {LocaleEntry} from '../types';
import mrMessages from '../locales/mr_IN.json';
import enUS from 'antd/lib/locale/en_US';

const MrLang: LocaleEntry = {
  messages: {
    ...mrMessages,
  },
  antLocale: enUS, // Ant Design doesn't have Marathi locale, using English as fallback
  locale: 'mr-IN',
  direction: 'ltr',
};
export default MrLang;
