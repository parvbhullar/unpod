import { ReactNode } from 'react';
import { MdBusinessCenter } from 'react-icons/md';
import { FaHeart, FaUser } from 'react-icons/fa';

export const PUBLIC_EMAIL_DOMAIN = [
  'gmail.com',
  'yahoo.co',
  'yahoo.co.in',
  'outlook.com',
  'hotmail.com',
  'microsoft.com',
  'yopmail.com',
  'icloud.com',
  'protonmail.com',
  'gmx.com',
  'mail.com',
  'fastmail.com',
  'zoho.com',
  'zohomail.in',
] as const;

export type PublicEmailDomain = (typeof PUBLIC_EMAIL_DOMAIN)[number];

export const GENDERS = {
  M: 'Male',
  F: 'Female',
} as const;

export type GenderKey = keyof typeof GENDERS;
export type GenderValue = (typeof GENDERS)[GenderKey];

export const LANGUAGE = {
  en: 'English',
  ar: 'Arabic',
  bn: 'Bengali',
  cs: 'Czech',
  da: 'Danish',
  de: 'German',
  el: 'Greek',
  es: 'Spanish',
  fi: 'Finnish',
  fil: 'Filipino',
  fr: 'French',
  gu: 'Gujarati',
  he: 'Hebrew',
  hi: 'Hindi',
  hu: 'Hungarian',
  id: 'Indonesian',
  it: 'Italian',
  ja: 'Japanese',
  ko: 'Korean',
  mr: 'Marathi',
  ms: 'Malay',
  nl: 'Dutch',
  no: 'Norwegian',
  pa: 'Punjabi',
  pl: 'Polish',
  pt: 'Portuguese',
  ro: 'Romanian',
  ru: 'Russian',
  sv: 'Swedish',
  ta: 'Tamil',
  te: 'Telugu',
  th: 'Thai',
  tr: 'Turkish',
  uk: 'Ukrainian',
  vi: 'Vietnamese',
  zh: 'Chinese',
} as const;

export type LanguageCode = keyof typeof LANGUAGE;
export type LanguageName = (typeof LANGUAGE)[LanguageCode];

// Deprecated: Use LANGUAGE instead
export const LANGUAGE_NAMES = new Proxy(
  {} as Record<string, string | undefined>,
  {
    get(_target, prop: string) {
      return LANGUAGE[prop.toLowerCase() as LanguageCode];
    },
  },
);

export type KeyFeature = {
  key: string;
  label: string;
};

export const KEY_FEATURES: KeyFeature[] = [
  {
    key: 'Sales & Leads',
    label: 'features.salesLeads',
  },
  {
    key: 'Support',
    label: 'features.support',
  },
  {
    key: 'Booking',
    label: 'features.booking',
  },
  {
    key: 'Front Desk',
    label: 'features.frontDesk',
  },
  {
    key: 'Custom',
    label: 'features.custom',
  },
];

export type PurposeCategory = {
  key: string;
  label: string;
  desc: string;
  icon: ReactNode;
  color: string;
};

export const PURPOSE_CATEGORIES: PurposeCategory[] = [
  {
    key: 'Business',
    label: 'identityOnboarding.businessFunctions',
    desc: 'identityOnboarding.businessFunctionsDesc',
    icon: <MdBusinessCenter size={24} />,
    color: '#9d5c06ff',
  },
  {
    key: 'Personal',
    label: 'identityOnboarding.personalFunctions',
    desc: 'identityOnboarding.personalFunctionsDesc',
    icon: <FaUser size={24} />,
    color: '#979492ff',
  },
  {
    key: 'Service',
    label: 'identityOnboarding.serviceFunctions',
    desc: 'identityOnboarding.serviceFunctionsDesc',
    icon: <FaHeart size={24} />,
    color: '#e70000ff',
  },
];

export type DayOption = {
  value: string;
  label: string;
};

export const DAYS: DayOption[] = [
  { value: 'Mon', label: 'advanced.dayMon' },
  { value: 'Tue', label: 'advanced.dayTue' },
  { value: 'Wed', label: 'advanced.dayWed' },
  { value: 'Thu', label: 'advanced.dayThu' },
  { value: 'Fri', label: 'advanced.dayFri' },
  { value: 'Sat', label: 'advanced.daySat' },
  { value: 'Sun', label: 'advanced.daySun' },
];
