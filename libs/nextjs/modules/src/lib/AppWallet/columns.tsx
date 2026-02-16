import { changeDateStringFormat } from '@unpod/helpers/DateHelper';
import { formatCredits } from '@unpod/helpers/NumberHelper';
import AppAmountView from '@unpod/components/common/AppAmountView';

type FormatMessage = (descriptor: { id: string }) => string;

export const getColumns = (
  currency: string,
  currentBitValue: number,
  formatMessage: FormatMessage,
) => {
  return [
    {
      title: formatMessage({ id: 'wallet.dateTime' }),
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      render: (text: string) => {
        return changeDateStringFormat(
          text,
          'YYYY-MM-DD HH:mm',
          'YYYY-MM-DD HH:mm',
        );
      },
    },
    {
      title: formatMessage({ id: 'wallet.credits' }),
      dataIndex: 'bits',
      key: 'bits',
      render: (text: number) => {
        return formatCredits(text);
      },
    },
    {
      title: formatMessage({ id: 'wallet.amount' }),
      dataIndex: 'bits',
      key: 'bits',
      render: (text: number) => (
        <AppAmountView amount={+text * currentBitValue} currency={currency} />
      ),
    },
    {
      title: formatMessage({ id: 'wallet.type' }),
      dataIndex: 'transaction_type',
      key: 'transaction_type',
    },
    {
      title: formatMessage({ id: 'wallet.via' }),
      dataIndex: 'transaction_via',
      key: 'transaction_via',
    },
  ];
};
