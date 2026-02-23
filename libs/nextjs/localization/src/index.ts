import enLang from './entries/en-US';
import arLang from './entries/ar-SA';
import bnLang from './entries/bn-BD';
import deLang from './entries/de-DE';
import esLang from './entries/es-ES';
import frLang from './entries/fr-FR';
import guLang from './entries/gu-IN';
import hiLang from './entries/hi-IN';
import itLang from './entries/it-IT';
import jaLang from './entries/ja-JP';
import koLang from './entries/ko-KR';
import mrLang from './entries/mr-IN';
import nlLang from './entries/nl-NL';
import paLang from './entries/pa-IN';
import plLang from './entries/pl-PL';
import ptLang from './entries/pt-PT';
import ruLang from './entries/ru-RU';
import taLang from './entries/ta-IN';
import teLang from './entries/te-IN';
import zhLang from './entries/zh-CN';

export type {LocaleEntry, LanguageData, Direction} from './types';

const AppLocale: Record<string, import('./types').LocaleEntry> = {
  en: enLang,
  ar: arLang,
  bn: bnLang,
  de: deLang,
  es: esLang,
  fr: frLang,
  gu: guLang,
  hi: hiLang,
  it: itLang,
  ja: jaLang,
  ko: koLang,
  mr: mrLang,
  nl: nlLang,
  pa: paLang,
  pl: plLang,
  pt: ptLang,
  ru: ruLang,
  ta: taLang,
  te: teLang,
  zh: zhLang,
};

export default AppLocale;
