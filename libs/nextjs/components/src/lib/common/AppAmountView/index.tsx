import React from 'react';

type AppAmountViewProps = {
  amount: string | number;
  currency?: string;
  decimalDigits?: number;
};

const AppAmountView: React.FC<AppAmountViewProps> = ({
                                                       amount,
                                                       currency = process.env.currency,
                                                       decimalDigits = 2,
                                                     }) => {
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: decimalDigits,
  });

  return <>{formatter.format(+amount || 0)}</>;
};

export default AppAmountView;
