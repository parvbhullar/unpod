declare module '@unpod/localization/languageData' {
  type LanguageItem = {
    locale: string;
    name: string;
    icon: string;};

  const languageData: LanguageItem[];
  export default languageData;
}
