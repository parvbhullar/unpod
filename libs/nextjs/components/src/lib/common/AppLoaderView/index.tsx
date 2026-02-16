import React from 'react';
import AppLoader from '../AppLoader';
import { useInfoViewContext } from '@unpod/providers';

const AppLoaderView = () => {
  const { loading } = useInfoViewContext();

  return loading && <AppLoader />;
};

export default React.memo(AppLoaderView);
