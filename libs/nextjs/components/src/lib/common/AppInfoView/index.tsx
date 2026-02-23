'use client';
import React, {useEffect} from 'react';
import {message} from 'antd';
import {useInfoViewActionsContext, useInfoViewContext,} from '@unpod/providers';
import AppLoader from '../AppLoader';

type AppInfoViewProps = {
  hideLoader?: boolean;
};

const AppInfoView: React.FC<AppInfoViewProps> = ({hideLoader = false}) => {
  const {loading, error, notification} = useInfoViewContext();
  const {clearAll} = useInfoViewActionsContext();
  const [messageApi, contextHolder] = message.useMessage();

  useEffect(() => {
    if (error) {
      messageApi
        .open({
          type: 'error',
          content: error,
        })
        .then(() => {
          clearAll();
        });
    }
  }, [error, clearAll, messageApi]);

  useEffect(() => {
    if (notification) {
      messageApi
        .open({
          type: 'success',
          content: notification,
        })
        .then(() => {
          clearAll();
        });
    }
  }, [notification, clearAll, messageApi]);

  return (
    <>
      {contextHolder}
      {loading && !hideLoader && <AppLoader/>}
    </>
  );
};

export default React.memo(AppInfoView);
