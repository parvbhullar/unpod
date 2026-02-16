export const formatCredits = (value: number | string, decimal = 3): string => {
  return parseFloat(parseFloat(String(value)).toFixed(decimal)).toLocaleString(
    'en-IN',
    {
      useGrouping: true,
    },
  );
};
