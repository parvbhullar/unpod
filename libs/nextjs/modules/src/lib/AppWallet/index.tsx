'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Space, Typography } from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import {
  postDataApi,
  putDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
  usePaginatedDataApi,
} from '@unpod/providers';
import { MdClose, MdOutlineAccountBalanceWallet } from 'react-icons/md';
import AddWallet from './AddWallet';
import { getOrderPayload } from '@unpod/helpers/PaymentHelper';
import { useRazorpay } from 'react-razorpay';
import ThreeColumnPageLayout from '@unpod/components/common/AppPageLayout/layouts/ThreeColumnPageLayout';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import { getColumns } from './columns';
import { isArray } from 'lodash';
import AppTable from '@unpod/components/third-party/AppTable';
import AppPageHeader, {
  AppHeaderButton,
} from '@unpod/components/common/AppPageHeader';
import { StyledHeader } from './index.styled';
import { formatCredits } from '@unpod/helpers/NumberHelper';
import { AppDrawer, AppPopover } from '@unpod/components/antd';
import { FiPlus } from 'react-icons/fi';
import AppLoadingMore from '@unpod/components/common/AppLoadingMore';
import { WalletSkeleton } from '@unpod/skeleton';
import { useIntl } from 'react-intl';

const { Paragraph, Text } = Typography;

type AppWalletModuleProps = {
  pageTitle: string;
};

type RazorpayResponse = {
  razorpay_payment_id?: string;
  [key: string]: any;
};

type BitDetail = {
  unit_value?: number;
};

type WalletDetail = {
  bits?: number;
};

const AppWalletModule = ({ pageTitle }: AppWalletModuleProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { Razorpay } = useRazorpay() as any;
  const { formatMessage } = useIntl();
  const { isAuthenticated, user, currency, subscription } = useAuthContext();

  const [addVisible, setAddVisible] = useState(false);
  const [currentTransactionId, setCurrentTransactionId] = useState(0);
  const [currentBitValue, setCurrentBitValue] = useState(0);
  const [loadingRazorPay, setLoadingRazorPay] = useState(false);
  const transactionId = useRef<number>(0);
  const { activeOrg } = useAuthContext();

  const [
    { apiData, isLoadingMore, loading, hasMoreRecord, page },
    { setLoadingMore, setPage, reCallAPI, setRefreshing },
  ] = usePaginatedDataApi<unknown[]>(
    `wallet/bit-transaction/`,
    [],
    {
      page: 1,
      page_size: 30,
    },
    false,
  );

  const [{ apiData: bitData }, { reCallAPI: reCallAPIBitDetails }] =
    useGetDataApi<BitDetail>(
      'wallet/bit-detail/',
      { data: {} },
      { currency: currency },
      false,
    );

  const [{ apiData: walletData }, { reCallAPI: recallWalletDetails }] =
    useGetDataApi<WalletDetail>('wallet/detail/', { data: {} }, {}, false);

  useEffect(() => {
    if (isAuthenticated && activeOrg) {
      reCallAPI();
      recallWalletDetails();
      reCallAPIBitDetails();
    }
  }, [isAuthenticated, activeOrg]);

  useEffect(() => {
    if (bitData?.data) {
      setCurrentBitValue(bitData.data.unit_value ?? 0);
    }
  }, [bitData?.data]);

  const activePlan = useMemo(() => {
    const orderMetadata = subscription?.subscription_data as any;
    return orderMetadata
      ? {
          ...orderMetadata.subscription_details,
          subscription_id: orderMetadata.subscription_id,
        }
      : {};
  }, [subscription]);

  const onShowAddWallet = () => {
    setAddVisible(true);
  };

  const onWalletAddClose = () => {
    setAddVisible(false);
  };

  const checkoutRazorpay = (
    amount: number,
    currency: string,
    orderId: string,
    response: RazorpayResponse,
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
      })
      .catch((error: any) => {
        failedTransaction(amount, currency, orderId);
        infoViewActionsContext.showError(error.message);
        onWalletAddClose();
        setLoadingRazorPay(false);
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
      setLoadingRazorPay,
      description,
    );

    const rzp1 = new Razorpay(options as any);

    rzp1.on('payment.failed', (response: RazorpayResponse) => {
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
    payment_response: RazorpayResponse,
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

        if (payload.pay_type === 'success') {
          recallWalletDetails();
          setRefreshing(true);
          setPage(1);
          onWalletAddClose();
          setLoadingRazorPay(false);
        }
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onAddAmount = (amount: number) => {
    // Convert In INR
    amount = amount * currentBitValue;
    const description = `Unpod - Add Bits`;
    setLoadingRazorPay(true);

    const payload = {
      amount: amount,
      currency: currency,
      notes: { message: 'To Recharge the Wallet' },
    };

    postDataApi('wallet/payment/create-order/', infoViewActionsContext, payload)
      .then((data: any) => {
        startRazorpay(
          data.data.amount,
          data.data.currency,
          data.data.id,
          description,
        );
      })
      .catch((error: any) => {
        setLoadingRazorPay(false);
        infoViewActionsContext.showError(error.message);
      });
  };
  const onEndReached = () => {
    if (hasMoreRecord && !isLoadingMore) {
      setLoadingMore(true);
      setPage(page + 1);
    }
  };

  const AppTableAny = AppTable as any;

  return (
    <>
      <AppPageHeader
        hideToggleBtn
        pageTitle={formatMessage({ id: pageTitle })}
        titleIcon={<MdOutlineAccountBalanceWallet fontSize={21} />}
        rightOptions={
          <Space align="center" size="middle">
            {activePlan.name && (
              <AppPopover
                title={activePlan.name}
                content={
                  <Paragraph className="mb-0">
                    {formatMessage({ id: 'wallet.currentPlanDes' })}
                  </Paragraph>
                }
                color="#87d068"
              >
                <AppHeaderButton
                  type="primary"
                  color="danger"
                  size="small"
                  shape="round"
                  ghost
                >
                  {activePlan.name}
                </AppHeaderButton>
              </AppPopover>
            )}

            <StyledHeader>
              <AppImage
                src="/images/wallet/dollar-icon.svg"
                alt="Dollar"
                height={16}
                width={16}
              />
              <Text strong>{formatCredits(walletData?.data?.bits || 0)}</Text>
            </StyledHeader>
            <AppHeaderButton
              type="primary"
              shape="round"
              onClick={onShowAddWallet}
              icon={<FiPlus />}
            >
              {formatMessage({ id: 'common.add' })}
            </AppHeaderButton>
          </Space>
        }
      />

      <AppPageContainer>
        <ThreeColumnPageLayout layoutType="full">
          {apiData?.length === 0 && loading ? (
            <WalletSkeleton />
          ) : (
            <AppTableAny
              columns={getColumns(
                currency || 'USD',
                currentBitValue,
                formatMessage,
              )}
              dataSource={isArray(apiData) ? apiData : []}
              rowKey={'token'}
              size="middle"
              pagination={false}
              onScrolledToBottom={onEndReached}
            />
          )}
          {isLoadingMore && <AppLoadingMore />}
        </ThreeColumnPageLayout>
      </AppPageContainer>

      <AppDrawer
        title={formatMessage({ id: 'wallet.addCredits' })}
        placement="right"
        onClose={onWalletAddClose}
        closable={false}
        closeIcon={<MdClose fontSize={16} />}
        open={addVisible}
      >
        <AddWallet
          loading={loadingRazorPay}
          onWalletAddClose={onWalletAddClose}
          onAddAmount={onAddAmount}
          currentBitValue={currentBitValue}
          walletAmount={formatCredits(walletData?.data?.bits || 0)}
        />
      </AppDrawer>
    </>
  );
};
export default AppWalletModule;
