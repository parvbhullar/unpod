'use client';

import { useRef, useState } from 'react';
import { Alert, Button, Typography } from 'antd';

import { useRazorpay } from 'react-razorpay';
import {
  postDataApi,
  putDataApi,
  useAuthActionsContext,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { getOrderPayload } from '@unpod/helpers/PaymentHelper';
import PlanList from './PlanList';
import AppLoader from '@unpod/components/common/AppLoader';
import { StyledSection, StyledSectionLeft } from '../../index.styled';
import { useRouter } from 'next/navigation';
import { useIntl } from 'react-intl';

const { Title, Text } = Typography;

const SubscriptionPlans = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { Razorpay } = useRazorpay();
  const { getSubscription } = useAuthActionsContext();
  const { user, activeOrg } = useAuthContext();
  const { formatMessage } = useIntl();

  const [currentTransactionId, setCurrentTransactionId] = useState(0);
  const [loading, setLoading] = useState(false);
  const transactionId = useRef(0);
  const router = useRouter();

  const [{ apiData, loading: planLoading }] = useGetDataApi<unknown[]>(
    `subscriptions/plans/`,
    { data: [] },
    {},
    true,
  );

  const checkoutRazorpay = (
    amount: number,
    currency: string,
    orderId: string,
    response: any,
  ) => {
    const payload = {
      payment_response: response,
      amount: amount,
      currency: currency,
      order_id: orderId,
    };

    postDataApi(
      'wallet/payment/complete-subscription-order/',
      infoViewActionsContext,
      {
        payload: payload,
      },
    )
      .then((data: any) => {
        successTransaction(amount, currency, orderId, response);
        infoViewActionsContext.showMessage(data.message);
        setLoading(false);
      })
      .catch((error: any) => {
        failedTransaction(amount, currency, orderId);
        infoViewActionsContext.showError(error.message);
        setLoading(false);
      });
  };

  const startRazorpay = (
    amount: number,
    currency: string,
    orderId: string,
    description: string,
  ) => {
    const options = getOrderPayload(
      amount,
      currency,
      orderId,
      user as any,
      checkoutRazorpay,
      failedTransaction,
      setLoading,
      description,
    );

    const rzp1 = new Razorpay(options as any);

    rzp1.on('payment.failed', (response: any) => {
      failedTransaction(amount, currency, orderId);
    });

    rzp1.open();

    initiatedTransaction(amount, currency, orderId);
  };

  const initiatedTransaction = (
    amount: number,
    currency: string,
    orderId: string,
  ) => {
    const data = {
      currency: currency,
      amount: amount.toString(),
      order_id: orderId,
      payment_mode: 'razorpay',
      status: 'initiated',
    };

    const payload = {
      pay_response: data,
      pay_type: 'initiated',
    };

    updateTransaction(payload);
  };

  const successTransaction = (
    amount: number,
    currency: string,
    orderId: string,
    payment_response: any,
  ) => {
    const data = {
      currency: currency,
      amount: amount.toString(),
      order_id: orderId,
      payment_mode: 'razorpay',
      status: 'success',
      payment_id: payment_response.razorpay_payment_id,
      id: currentTransactionId,
    };

    const payload = {
      pay_response: data,
      pay_type: 'success',
    };

    updateTransaction(payload);
  };

  const failedTransaction = (
    amount: number,
    currency: string,
    orderId: string,
  ) => {
    const data = {
      currency: currency,
      amount: amount.toString(),
      order_id: orderId,
      payment_mode: 'razorpay',
      status: 'failed',
    };

    const payload = {
      pay_response: data,
      pay_type: 'failed',
    };

    updateTransaction(payload);
  };

  const updateTransaction = (payload: any) => {
    const pay_type = payload.pay_type;
    if (pay_type !== 'initiated') {
      payload.pay_response['id'] = transactionId.current;
    }

    putDataApi('wallet/payment/transaction-status/', infoViewActionsContext, {
      payload: payload,
    })
      .then((response: any) => {
        const data = response.data;
        setCurrentTransactionId(data.id);
        transactionId.current = data.id;

        if (payload.pay_type === 'success') {
          getSubscription();
          router.replace('/billing');
        }
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onActivatePlan = (plan: any) => {
    setLoading(true);

    const payload = {
      subscription_id: plan.id,
    };

    const description = formatMessage(
      { id: 'common.subscriptionDes' },
      { name: plan.name },
    );

    postDataApi(
      'wallet/payment/create-subscription-order/',
      infoViewActionsContext,
      payload,
    )
      .then((data: any) => {
        if (plan.price > 0) {
          startRazorpay(
            data.data.amount,
            data.data.currency,
            data.data.id,
            description,
          );
        } else {
          getSubscription();
          infoViewActionsContext.showMessage(
            data.message || formatMessage({ id: 'subscription.planActive' }),
          );
          setLoading(false);
        }
      })
      .catch((error: any) => {
        setLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  const onCancelSubscription = (plan: any) => {
    setLoading(true);

    const payload = {
      subscription_id: plan.id,
    };

    postDataApi('wallet/subscription-cancel/', infoViewActionsContext, payload)
      .then((data: any) => {
        getSubscription();
        infoViewActionsContext.showMessage(
          data.message ||
            formatMessage({ id: 'subscription.subscriptionCancel' }),
        );
        setLoading(false);
      })
      .catch((error: any) => {
        setLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  const handleContactPlan = (plan: any) => {
    setLoading(true);
    const payload = {
      plan_id: plan.id,
    };
    postDataApi(
      'subscriptions/request-subscription/',
      infoViewActionsContext,
      payload,
    )
      .then((data: any) => {
        infoViewActionsContext.showMessage(
          data.message || formatMessage({ id: 'common.sendRequest' }),
        );
        setLoading(false);
      })
      .catch((error: any) => {
        setLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  if (planLoading) {
    return <AppLoader />;
  }

  const orgBillingEmail = (
    activeOrg as { billing_info?: { email?: string } } | null
  )?.billing_info?.email;

  return (
    <>
      {!orgBillingEmail && (
        <Alert
          type="warning"
          showIcon
          message={formatMessage({ id: 'upgrade.alertMessage' })}
          action={
            <Button
              size="small"
              type="primary"
              ghost
              onClick={() => router.push('/billing/info')}
            >
              {formatMessage({ id: 'billing.addInfo' })}
            </Button>
          }
        />
      )}
      <StyledSection>
        <StyledSectionLeft>
          <Title level={3} style={{ margin: 0 }}>
            {formatMessage({ id: 'upgrade.choosAPlan' })}
          </Title>
          <Text type={'secondary'}>
            {formatMessage({ id: 'upgrade.description' })}
          </Text>
        </StyledSectionLeft>
      </StyledSection>
      <PlanList
        plans={apiData?.data || []}
        loading={loading}
        onActivatePlan={onActivatePlan}
        onCancelSubscription={onCancelSubscription}
        onContactPlan={handleContactPlan}
      />
    </>
  );
};

export default SubscriptionPlans;
