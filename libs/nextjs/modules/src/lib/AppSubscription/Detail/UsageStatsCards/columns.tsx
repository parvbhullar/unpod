import { MdAccessTime, MdCreditCard, MdDescription } from 'react-icons/md';
import { changeDateStringFormat } from '@unpod/helpers/DateHelper';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';

type FormatMessage = (descriptor: { id: string }) => string;

export const getColumns = (subscription: any, formatMessage: FormatMessage) => {
  return [
    {
      id: 'minUseToday',
      name: formatMessage({ id: 'usageStatsCards.minUseToday' }),
      value: subscription?.usage_stats.today_minutes || 0,
      unit: formatMessage({ id: 'common.mins' }),
      subText: formatMessage({ id: 'usageStatsCards.minSubText' }),
      icon: <MdAccessTime size={28} color="#555" />,
    },
    {
      id: 'minUseMonth',
      name: formatMessage({ id: 'usageStatsCards.minUseMonth' }),
      value: subscription?.usage_stats.month_minutes || 0,
      unit: formatMessage({ id: 'common.mins' }),
      subText: formatMessage({ id: 'usageStatsCards.monthSubText' }),
      icon: <MdDescription size={28} color="#555" />,
    },
    {
      id: 'currentInvoice',
      name: formatMessage({ id: 'usageStatsCards.currentInvoice' }),
      value: getAmountWithCurrency(subscription?.invoice?.amount || 0),
      unit: '',
      subText: changeDateStringFormat(
        subscription?.invoice.invoice_date,
        'YYYY-MM-DD',
        'MMMM YYYY',
      ),
      icon: <MdCreditCard size={28} color="#555" />,
    },
  ];
};
