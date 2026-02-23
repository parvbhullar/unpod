import type {LocaleEntry} from '../types';
import hiMessages from '../locales/hi_IN.json';
import hiIN from 'antd/lib/locale/hi_IN';

const HiLang: LocaleEntry = {
  messages: {
    ...hiMessages,
  },
  antLocale: hiIN,
  locale: 'hi-IN',
  direction: 'ltr',
};
export default HiLang;
