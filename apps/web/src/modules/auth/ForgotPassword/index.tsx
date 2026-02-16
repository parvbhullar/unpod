'use client';
import React, { useState } from 'react';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import ForgotPasswordForm from './ForgotPasswordForm';
import ResetLinkSent from './ResetLinkSent';
import { Card } from 'antd';
import { StyledAuthContainer } from '@/modules/auth/auth.styled';

const ForgotPassword = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [resetLinkSent, setResetLinkSent] = useState(false);

  const onSubmit = (data: { email?: string }) => {
    postDataApi('password/forgot/', infoViewActionsContext, data)
      .then((response) => {
        const payload = response as { message?: string };
        infoViewActionsContext.showMessage(payload.message || 'Link sent');
        setResetLinkSent(true);
      })
      .catch((response) => {
        const payload = response as { message?: string };
        infoViewActionsContext.showError(
          payload.message || 'Failed to send link',
        );
      });
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          {resetLinkSent ? (
            <ResetLinkSent />
          ) : (
            <ForgotPasswordForm onSubmit={onSubmit} />
          )}
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default ForgotPassword;
