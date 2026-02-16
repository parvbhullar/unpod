import { useEffect, useRef, useState } from 'react';
import { MdClose } from 'react-icons/md';
import type { RazorpayOrderOptions } from 'react-razorpay';
import { useRazorpay } from 'react-razorpay';
import { formatCredits } from '@unpod/helpers/NumberHelper';
import {
  postDataApi,
  putDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { getOrderPayload } from '@unpod/helpers/PaymentHelper';
import AddCreditForm from './AddCreditForm';
import AppDrawer from '../../antd/AppDrawer';

type AppAddAmountProps = {
  open: boolean;
  setOpen: (open: boolean) => void;};

const AppAddAmount = ({ open, setOpen }: AppAddAmountProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { Razorpay } = useRazorpay();
  const { user, currency } = useAuthContext();

  const [currentTransactionId, setCurrentTransactionId] = useState(0);
  const [currentBitValue, setCurrentBitValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const transactionId = useRef(0);

  const [{ apiData: bitData }] = useGetDataApi<any>(
    'wallet/bit-detail/',
    { data: {} },
    { currency: currency },
  );
  const [{ apiData: walletData }] = useGetDataApi<any>('wallet/detail/', {
    data: {},
  });

  useEffect(() => {
    if (bitData?.data) {
      setCurrentBitValue(bitData?.data.unit_value);
    }
  }, [bitData?.data]);

  const onClose = () => {
    setOpen(false);
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
      'wallet/payment/complete-transaction/',
      infoViewActionsContext,
      {
        payload: payload,
      },
    )
      .then((data: any) => {
        successTransaction(amount, currency, orderId, response);
        infoViewActionsContext.showMessage(data.message);
        onClose();
        setLoading(false);
      })
      .catch((error: any) => {
        failedTransaction(amount, currency, orderId);
        infoViewActionsContext.showError(error.message);
        onClose();
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
      user,
      checkoutRazorpay,
      failedTransaction,
      setLoading,
      description,
    ) as unknown as RazorpayOrderOptions;

    const rzp1 = new Razorpay(options);

    rzp1.on('payment.failed', (response: any) => {
      console.log('payment Failed', response);
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
      .then(({ data }: any) => {
        setCurrentTransactionId(data.id);
        transactionId.current = data.id;
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onAddAmount = (amount: number) => {
    amount = amount * currentBitValue;
    const description = `Unpod - Add Bits`;
    setLoading(true);

    const payload = {
      amount: amount,
      currency: currency,
      notes: { message: 'To Recharge the Wallet' },
    };

    postDataApi('wallet/payment/create-order/', infoViewActionsContext, payload)
      .then((data: any) => {
        startRazorpay(amount, currency!, data.data.id, description);
      })
      .catch((error: any) => {
        setLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  return (
    <AppDrawer
      title="Add Credits"
      placement="right"
      onClose={onClose}
      closable={false}
      closeIcon={<MdClose fontSize={16} />}
      open={open}
    >
      <AddCreditForm
        loading={loading}
        onWalletAddClose={onClose}
        onAddAmount={onAddAmount}
        walletAmount={formatCredits(walletData.data?.bits || 0)}
      />
    </AppDrawer>
  );
};

export default AppAddAmount;
