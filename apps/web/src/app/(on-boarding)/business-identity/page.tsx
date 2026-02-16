import React, { Fragment } from 'react';
import BusinessIdentity from '@/modules/BusinessIdentity';
import AppInfoView from '@unpod/components/common/AppInfoView';

export async function generateMetadata() {
  return {
    title: 'Business Identity | Unpod',
    description:
      'Set up your business identity to enhance your Unpod experience.',
  };
}

const BusinessIdentityPage = () => {
  return (
    <Fragment>
      <AppInfoView hideLoader />
      <BusinessIdentity />
    </Fragment>
  );
};

export default BusinessIdentityPage;
