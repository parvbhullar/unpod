'use client';
import { Fragment } from 'react';
import { MdOutlineAccountBalanceWallet } from 'react-icons/md';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import { useAuthContext } from '@unpod/providers';
import PageBaseHeader from '@unpod/components/common/AppPageLayout/layouts/ThreeColumnPageLayout/PageBaseHeader';
import { StyledContainer } from './index.styled';
import ViewBillingInfo from './ViewBilling';
import BillingInfoSkeleton from '@unpod/skeleton/BillingInfoSkeleton';

const BillingInfo = () => {
  const { user } = useAuthContext();

  return (
    <Fragment>
      <PageBaseHeader
        pageTitle="Billing Information"
        titleIcon={<MdOutlineAccountBalanceWallet fontSize={24} />}
        hideToggleBtn
      />

      <AppPageContainer>
        {!user ? (
          <BillingInfoSkeleton />
        ) : (
          <StyledContainer>
            <ViewBillingInfo />
          </StyledContainer>
        )}
      </AppPageContainer>
    </Fragment>
  );
};

export default BillingInfo;
