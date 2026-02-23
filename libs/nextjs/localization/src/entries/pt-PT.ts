import type {LocaleEntry} from '../types';
import ptMessages from '../locales/pt_PT.json';
import ptPT from 'antd/lib/locale/pt_PT';

const PtLang: LocaleEntry = {
  messages: {
    ...ptMessages,
  },
  antLocale: ptPT,
  locale: 'pt-PT',
  direction: 'ltr',
};
export default PtLang;
