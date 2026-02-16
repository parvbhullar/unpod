import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Divider, Flex, Typography } from 'antd';
import { useRazorpay } from 'react-razorpay';
import { getOrderPayload } from '@unpod/helpers/PaymentHelper';
import AppTable from '@unpod/components/third-party/AppTable';
import AppAmountView from '@unpod/components/common/AppAmountView';
import {
  getAllItemsAmount,
  getAllTaxAmount,
  getItemAmount,
  getTotalAmount,
} from '@unpod/helpers/CalculationHelper';
import {
  postDataApi,
  putDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { getColumns } from './columns';
import {
  StyledContainer,
  StyledContent,
  StyledRoot,
  StyledText,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Text, Title } = Typography;

const AppTableAny = AppTable as any;
const AlertAny = Alert as any;

const SubscriptionAddOns = ({
  setAddonOpen,
}: {
  setAddonOpen: (open: boolean) => void;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { Razorpay } = useRazorpay();
  const { user, currency, subscription } = useAuthContext();
  const { getSubscription } = useAuthActionsContext();
  const { formatMessage } = useIntl();

  const [modules, setModules] = useState<any[]>([]);
  const [isPaymentLoading, setPaymentLoading] = useState(false);
  const transactionId = useRef(0);

  useEffect(() => {
    if (subscription?.modules)
      setModules(
        (subscription as any).modules
          .filter((mod: any) => !mod.is_unlimited && mod.price_type !== 'fixed')
          .map((mod: any) => {
            return {
              ...mod,
              quantity: 0,
            };
          }),
      );
  }, [subscription]);

  const handleAddChange = (codename: string, quantity: number) => {
    setModules((prev: any[]) =>
      prev.map((mod: any) =>
        mod.codename === codename ? { ...mod, quantity: quantity || 0 } : mod,
      ),
    );
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
        const data = response?.data || response;
        transactionId.current = data?.id;

        if (payload.pay_type === 'success') {
          getSubscription();
          setAddonOpen(false);
        }
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

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
      'wallet/payment/complete-addon-subscription-order/',
      infoViewActionsContext,
      payload,
    )
      .then((data: any) => {
        successTransaction(amount, currency, orderId, response);
        infoViewActionsContext.showMessage(data.message);
        setPaymentLoading(false);
      })
      .catch((error: any) => {
        failedTransaction(amount, currency, orderId);
        infoViewActionsContext.showError(error.message);
        setPaymentLoading(false);
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
      setPaymentLoading,
      description,
    );

    const rzp1 = new Razorpay(options as any);

    rzp1.on('payment.failed', (response: any) => {
      console.log('payment failed', response, amount, currency, orderId);
      failedTransaction(amount, currency, orderId);
    });

    rzp1.open();

    initiatedTransaction(amount, currency, orderId);
  };

  const onSubmit = () => {
    const addons = modules
      .filter((mod: any) => mod.quantity > 0 && getItemAmount(mod) > 0)
      .reduce((acc: any[], mod: any) => {
        acc.push({
          codename: mod.codename,
          quantity: mod.quantity,
        });
        return acc;
      }, []);

    if (addons.length === 0) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'addons.ErrorMessage' }),
      );
      return;
    }

    setPaymentLoading(true);

    const payload = {
      currency: currency,
      addons: addons,
    };

    postDataApi(
      'wallet/payment/create-addon-subscription-order/',
      infoViewActionsContext,
      payload,
    )
      .then((data: any) => {
        startRazorpay(
          data.data.amount,
          data.data.currency,
          data.data.id,
          data.data.description,
        );
      })
      .catch((error: any) => {
        setPaymentLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <StyledRoot>
      <AlertAny
        type="info"
        showIcon
        message={formatMessage({ id: 'addons.alertMessage' })}
      />

      <AppTableAny
        rowKey={'key'}
        columns={getColumns(handleAddChange, formatMessage)}
        dataSource={modules}
        pagination={false}
        bordered={false}
        size="large"
        fullHeight={400}
        style={{ blockSize: 'auto' }}
      />

      <StyledContent>
        <Title level={5}>{formatMessage({ id: 'addons.orderSummary' })}</Title>
        <Flex vertical gap={4} style={{ marginTop: 8 }}>
          {modules.map((item: any) => (
            <Flex key={item.codename} justify="space-between">
              <StyledText strong>{item.module_name}:</StyledText>
              <AppAmountView amount={getItemAmount(item)} />
            </Flex>
          ))}

          <Flex justify="space-between">
            <Text strong>{formatMessage({ id: 'addons.subtotal' })}</Text>
            <Text strong>
              <AppAmountView amount={getAllItemsAmount(modules)} />
            </Text>
          </Flex>
          <Flex justify="space-between">
            <Text>{formatMessage({ id: 'addons.taxAmount' })}</Text>
            <AppAmountView amount={getAllTaxAmount(modules)} />
          </Flex>
          <Divider style={{ margin: '8px 0' }} />
          <Flex justify="space-between">
            <Text strong>{formatMessage({ id: 'addons.totalAmount' })}</Text>
            <Text strong>
              <AppAmountView amount={getTotalAmount(modules)} />
            </Text>
          </Flex>
        </Flex>
      </StyledContent>

      <StyledContainer>
        <Flex justify="end" gap={8}>
          <Button
            onClick={() => setAddonOpen(false)}
            loading={isPaymentLoading}
          >
            {formatMessage({ id: 'common.cancel' })}
          </Button>
          <Button type="primary" onClick={onSubmit} loading={isPaymentLoading}>
            {formatMessage({ id: 'addons.addSubscriptionButton' })}
          </Button>
        </Flex>
      </StyledContainer>
    </StyledRoot>
  );
};

export default SubscriptionAddOns;
