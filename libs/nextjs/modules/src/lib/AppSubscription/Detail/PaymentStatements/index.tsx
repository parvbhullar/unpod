import { useRef, useState } from 'react';
import { useRazorpay } from 'react-razorpay';
import { getOrderPayload } from '@unpod/helpers/PaymentHelper';
import {
  postDataApi,
  putDataApi,
  useAuthContext,
  useDownloadData,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import CardWrapper from '../../CardWrapper';
import { getColumns } from './columns';
import AppTable from '@unpod/components/third-party/AppTable';
import { useIntl } from 'react-intl';

const AppTableAny = AppTable as any;

const PaymentStatements = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();
  const { Razorpay } = useRazorpay();
  const { user } = useAuthContext();

  const [isPaymentLoading, setPaymentLoading] = useState(false);
  const transactionId = useRef(0);

  const [{ apiData, loading }, { reCallAPI }] = useGetDataApi(
    'subscriptions/user-invoices/',
    { data: [] },
    {},
    true,
  ) as any;
  const { downloading, downloadData } = useDownloadData(
    'subscriptions/user-invoices/download/',
    'invoice.pdf',
    'application/pdf',
    'arraybuffer',
  );

  const onDownloadInvoice = (item: any) => {
    downloadData(
      {},
      `invoice-${item.invoice_number}.pdf`,
      `subscriptions/user-invoices/${item.invoice_number}/download/`,
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
          reCallAPI();
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
      'wallet/payment/complete-invoice-payment/',
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

  const onPayInvoice = (item: any) => {
    setPaymentLoading(true);

    const payload = {
      invoice_number: item.invoice_number,
    };

    postDataApi('wallet/payment/pay-invoice/', infoViewActionsContext, payload)
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
    <CardWrapper
      title={formatMessage({ id: 'billing.paymentTitle' })}
      subtitle=""
      desc={formatMessage({ id: 'billing.paymentDes' })}
    >
      <AppTableAny
        loading={loading || downloading}
        columns={getColumns(
          onDownloadInvoice,
          onPayInvoice,
          isPaymentLoading,
          formatMessage,
        )}
        dataSource={(apiData as any)?.data || []}
        pagination={false}
        bordered={false}
        fullHeight
        size="large"
      />
    </CardWrapper>
  );
};

export default PaymentStatements;
