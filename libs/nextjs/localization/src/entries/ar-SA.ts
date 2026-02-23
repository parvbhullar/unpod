import type {LocaleEntry} from '../types';
import arMessages from '../locales/ar_SA.json';
import arEG from 'antd/lib/locale/ar_EG';

const ArLang: LocaleEntry = {
  messages: {
    ...arMessages,
  },
  antLocale: arEG,
  locale: 'ar-SA',
  direction: 'rtl',
};
export default ArLang;
