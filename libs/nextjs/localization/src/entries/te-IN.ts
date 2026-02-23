import type {LocaleEntry} from '../types';
import teMessages from '../locales/te_IN.json';
import enUS from 'antd/lib/locale/en_US';

const TeLang: LocaleEntry = {
  messages: {
    ...teMessages,
  },
  antLocale: enUS, // Ant Design doesn't have Telugu locale, using English as fallback
  locale: 'te-IN',
  direction: 'ltr',
};
export default TeLang;
