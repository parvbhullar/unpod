'use client';
import React from 'react';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import ResetForm from './ResetForm';
import PasswordChanged from './PasswordChanged';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { StyledAuthContainer } from '@/modules/auth/auth.styled';
import { Card } from 'antd';

type ResetPasswordProps = {
  token?: string | null;
};

const ResetPassword = ({ token }: ResetPasswordProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [passwordChanged, setPasswordChanged] = React.useState(false);

  const onPasswordReset = (postData: { password?: string }) => {
    if (token)
      postDataApi<unknown>('password/reset/confirm/', infoViewActionsContext, {
        user_token: token,
        password: postData.password,
      })
        .then((data) => {
          const payload = data;
          setPasswordChanged(true);
          infoViewActionsContext.showMessage(payload?.message || '');
        })
        .catch((error) => {
          const payload = error as { message?: string };
          infoViewActionsContext.showError(payload?.message || '');
        });
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          {passwordChanged ? (
            <PasswordChanged />
          ) : (
            <ResetForm onPasswordReset={onPasswordReset} />
          )}
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default ResetPassword;
