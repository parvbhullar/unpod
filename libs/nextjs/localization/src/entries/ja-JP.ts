import type {LocaleEntry} from '../types';
import jaMessages from '../locales/ja_JP.json';
import jaJP from 'antd/lib/locale/ja_JP';

const JaLang: LocaleEntry = {
  messages: {
    ...jaMessages,
  },
  antLocale: jaJP,
  locale: 'ja-JP',
  direction: 'ltr',
};
export default JaLang;
