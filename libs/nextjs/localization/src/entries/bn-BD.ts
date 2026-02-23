import type {LocaleEntry} from '../types';
import bnMessages from '../locales/bn_BD.json';
import bnBD from 'antd/lib/locale/bn_BD';

const BnLang: LocaleEntry = {
  messages: {
    ...bnMessages,
  },
  antLocale: bnBD,
  locale: 'bn-BD',
  direction: 'ltr',
};
export default BnLang;
