import { User } from '@unpod/constants';

export type RazorpayResponse = {
  razorpay_payment_id?: string;
  razorpay_order_id?: string;
  razorpay_signature?: string;};

export type OrderPayload = {
  key: string | undefined;
  currency: string;
  amount: string;
  order_id: string;
  name: string;
  description: string;
  image: string;
  handler: (response: RazorpayResponse) => void;
  modal: {
    ondismiss: () => void;
  };
  prefill: {
    name: string | undefined;
    email: string | undefined;
    contact: string | undefined;
  };
  theme: {
    color: string;
  };};

export const getOrderPayload = (
  amount: number,
  currency: string,
  orderId: string,
  user: User | null,
  checkoutRazorpay: (
    amount: number,
    currency: string,
    orderId: string,
    response: RazorpayResponse,
  ) => void,
  failedTransaction: (
    amount: number,
    currency: string,
    orderId: string,
  ) => void,
  setLoading: (loading: boolean) => void,
  description = 'Unpod Add Bits',
): OrderPayload => {
  return {
    key: process.env.paymentGatewayKey,
    currency: currency,
    amount: amount.toString(),
    order_id: orderId,
    name: 'Unpod',
    description: description,
    image: '/images/logo.png',
    handler: (response: RazorpayResponse) => {
      console.log('payment success', response, amount, currency, orderId);
      checkoutRazorpay(amount, currency, orderId, response);
    },
    modal: {
      ondismiss: () => {
        console.log('checkout cancelled', amount, currency, orderId);
        failedTransaction(amount, currency, orderId);
        setLoading(false);
      },
    },
    prefill: {
      name: user?.full_name,
      email: user?.email,
      contact: user?.phone_number,
    },
    theme: {
      color: '#528FF0',
    },
  };
};

export type SubscriptionModule = {
  codename?: string;
  remaining?: number;
  [key: string]: unknown;};

export const getSubscriptionModule = (
  modules: SubscriptionModule[] | null | undefined,
  moduleCodeName: string,
): SubscriptionModule => {
  return modules?.find((m) => m.codename === moduleCodeName) || {};
};

export const getRemainingChannels = (
  modules: SubscriptionModule[] | null | undefined,
): number => {
  const channelPlan = getSubscriptionModule(modules, 'channels');
  return channelPlan ? channelPlan.remaining || 0 : 0;
};
