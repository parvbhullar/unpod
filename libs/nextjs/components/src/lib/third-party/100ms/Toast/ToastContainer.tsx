import React, { useEffect, useState } from 'react';
// import { selectIsConnectedToRoom, useHMSStore } from '@100mslive/react-sdk';
import { Toast } from './Toast';
import { ToastManager } from './ToastManager';

export const ToastContainer = () => {
  // const isConnected = useHMSStore(selectIsConnectedToRoom);
  const [toasts, setToast] = useState([]);
  useEffect(() => {
    ToastManager.addListener(setToast);
    return () => {
      ToastManager.removeListener(setToast);
    };
  }, []);

  return (
    <>
      {toasts.slice(0, 2).map((toast) => {
        return (
          <Toast
            key={toast.id}
            {...toast}
            onOpenChange={(value) =>
              !value && ToastManager.removeToast(toast.id)
            }
          />
        );
      })}
    </>
  );
};
