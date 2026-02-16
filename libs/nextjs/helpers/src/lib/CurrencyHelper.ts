export const getCurrencySymbol = (
  currency = process.env.currency || 'USD',
  locale = 'en-US',
): string => {
  return (0)
    .toLocaleString(locale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
    .replace(/\d/g, '')
    .trim();
};

export const getAmountWithCurrency = (
  amount: number | string | null | undefined,
  currency = process.env.currency || 'USD',
  decimalDigits = 2,
  locale = 'en-US',
): string => {
  return (amount ? +amount : 0).toLocaleString(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: decimalDigits,
  });
};
