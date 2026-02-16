import CardWrapper from '../../CardWrapper';
import { getColumns } from './columns';
import { getFormattedDate } from '@unpod/helpers/DateHelper';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';
import AppTable from '@unpod/components/third-party/AppTable';
import { useIntl } from 'react-intl';

const AppTableAny = AppTable as any;

const MonthlyUsageReport = ({ subscription }: { subscription: any }) => {
  const { formatMessage } = useIntl();
  const plan = subscription?.subscription;

  let totalPrice = +plan?.price;

  // Start with the subscription plan data
  const servicesData = [
    {
      serviceName: `${plan?.name} ${formatMessage({ id: 'billing.subscription' })}`,
      allocated: '-',
      consumed: '-',
      remaining: '-',
      cost: getAmountWithCurrency(plan?.price || 0),
    },
  ];

  // Add consumption data to servicesData if it exists
  if (subscription?.modules) {
    const consumptionData = Object.entries(
      (subscription as any)?.modules || {},
    ).map((item) => {
      const [, serviceData] = item as any;
      totalPrice += serviceData?.total_cost || 0;
      return {
        ...(serviceData || {}),
        serviceName: `${serviceData?.display_name} (${
          serviceData?.unit === 'minute' ? 'min' : serviceData?.unit
        }s)`,
        cost: getAmountWithCurrency(serviceData?.total_cost || 0),
      };
    });

    servicesData.push(...consumptionData);
  }

  return (
    <CardWrapper
      title={`${getFormattedDate(new Date(), 'MMMM YYYY')} Usage`}
      subtitle=""
      desc=""
    >
      <AppTableAny
        columns={getColumns(formatMessage)}
        dataSource={subscription?.has_subscription ? servicesData : []}
        pagination={false}
        bordered={false}
        fullHeight
        size="middle"
      />
    </CardWrapper>
  );
};

export default MonthlyUsageReport;
