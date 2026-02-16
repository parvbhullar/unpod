import { Fragment, useState } from 'react';
import { Button, Flex, Space, Typography } from 'antd';
import { MdAdd } from 'react-icons/md';
import { FiCalendar } from 'react-icons/fi';
import { useRouter } from 'next/navigation';
import { LuCreditCard } from 'react-icons/lu';

import { AppDrawer } from '@unpod/components/antd';
import { getAmountWithCurrency } from '@unpod/helpers/CurrencyHelper';
import { useAuthContext } from '@unpod/providers';
import { changeDateStringFormat } from '@unpod/helpers/DateHelper';
import CardWrapper from '../../CardWrapper';
import SubscriptionAddOns from './SubscriptionAddOns';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';
import { useIntl } from 'react-intl';

const { Text } = Typography;

const ActivePlanSummary = ({ subscription }: { subscription: any }) => {
  const plan = subscription?.subscription;
  const router = useRouter();
  const { activeOrg } = useAuthContext();
  const [isAddonOpen, setAddonOpen] = useState(false);
  const { formatMessage } = useIntl();

  const mobileScreen = useMediaQuery(MobileWidthQuery);

  let allowAddons = false;

  if (subscription?.has_subscription && subscription?.modules) {
    for (const mod of (subscription as any).modules) {
      if (!mod.is_unlimited && mod.price_type !== 'fixed') {
        allowAddons = true;
        break;
      }
    }
  }

  return (
    <Fragment>
      <CardWrapper
        title={formatMessage({ id: 'billing.currentPlan' })}
        subtitle={plan?.plan_name}
        desc={
          plan?.description || formatMessage({ id: 'billing.noActivePlan' })
        }
      >
        <div className="row-inline">
          <Flex
            gap={8}
            align={mobileScreen ? 'flex-start' : 'center'}
            vertical={mobileScreen && true}
          >
            <Flex gap={8} align="center" justify="center">
              <Text type="secondary">
                <FiCalendar size={16} />
              </Text>
              <Text type="secondary">
                {formatMessage({ id: 'billing.nextBillingCycle' })}{' '}
                {subscription?.has_subscription
                  ? changeDateStringFormat(
                      plan?.next_billing_date,
                      'YYYY-MM-DD',
                      'D MMMM YYYY',
                    )
                  : 'N/A'}
              </Text>
            </Flex>
            <Flex gap={8} align="center">
              <Text type="secondary">
                <LuCreditCard size={18} />
              </Text>
              <Text type="secondary">
                {formatMessage({ id: 'billing.lastInvoice' })}{' '}
                {getAmountWithCurrency(subscription?.invoice?.amount)}
              </Text>
            </Flex>
          </Flex>

          <Space wrap>
            <Button
              type="default"
              style={{ padding: '10px' }}
              size="small"
              onClick={() => router.push('/wallet')}
            >
              {formatMessage({ id: 'billing.creditBalance' })}
            </Button>
            <Button
              type="default"
              style={{ padding: '10px' }}
              size="small"
              onClick={() => router.push('/billing/info')}
            >
              {(activeOrg as any)?.billing_info?.email
                ? formatMessage({ id: 'billing.info' })
                : formatMessage({ id: 'billing.addInfo' })}
            </Button>
            {allowAddons && (
              <Button
                type="primary"
                style={{ padding: '10px' }}
                size="small"
                onClick={() => setAddonOpen(true)}
                icon={<MdAdd size={16} />}
              >
                {formatMessage({ id: 'billing.addOn' })}
              </Button>
            )}
          </Space>
        </div>
      </CardWrapper>

      {allowAddons && (
        <AppDrawer
          isCallFilterView
          closable={false}
          title="Add Subscription Add-ons"
          open={isAddonOpen}
          onClose={() => setAddonOpen(false)}
          width={800}
        >
          <SubscriptionAddOns setAddonOpen={setAddonOpen} />
        </AppDrawer>
      )}
    </Fragment>
  );
};

export default ActivePlanSummary;
