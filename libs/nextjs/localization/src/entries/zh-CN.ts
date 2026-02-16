import type { LocaleEntry } from '../types';
import zhMessages from '../locales/zh_CN.json';
import zhCN from 'antd/lib/locale/zh_CN';

const ZhLang: LocaleEntry = {
  messages: {
    ...zhMessages,
  },
  antLocale: zhCN,
  locale: 'zh-CN',
  direction: 'ltr',
};
export default ZhLang;
