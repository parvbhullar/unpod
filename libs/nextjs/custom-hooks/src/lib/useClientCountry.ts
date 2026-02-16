import { useEffect, useState } from 'react';

const DEFAULT_COUNTRY = 'in';

export const useClientCountry = (): string => {
  const [countryCode, setCountryCode] = useState<string>(DEFAULT_COUNTRY);

  useEffect(() => {
    const getCurrentUserCountry = (): void => {
      const locale =
        navigator.language || (navigator.languages && navigator.languages[0]);
      if (locale) {
        const code = locale.split('-')[1]?.toLowerCase();
        if (code) {
          setCountryCode(DEFAULT_COUNTRY);
          return;
        }
      }
    };
    getCurrentUserCountry();
  }, []);

  return countryCode;
};
