import type {LocaleEntry} from '../types';
import taMessages from '../locales/ta_IN.json';
import enUS from 'antd/lib/locale/en_US';

const TaLang: LocaleEntry = {
  messages: {
    ...taMessages,
  },
  antLocale: enUS, // Ant Design doesn't have Tamil locale, using English as fallback
  locale: 'ta-IN',
  direction: 'ltr',
};
export default TaLang;
