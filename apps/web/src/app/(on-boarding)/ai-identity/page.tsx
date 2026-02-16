import OnBoarding from '@/modules/Onboarding';
import AppInfoView from '@unpod/components/common/AppInfoView';
import React from 'react';

export default function HomePage() {
  return (
    <>
      <AppInfoView hideLoader />
      <OnBoarding />
    </>
  );
}
