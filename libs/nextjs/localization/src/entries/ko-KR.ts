import type {LocaleEntry} from '../types';
import koMessages from '../locales/ko_KR.json';
import koKR from 'antd/lib/locale/ko_KR';

const KoLang: LocaleEntry = {
  messages: {
    ...koMessages,
  },
  antLocale: koKR,
  locale: 'ko-KR',
  direction: 'ltr',
};
export default KoLang;
