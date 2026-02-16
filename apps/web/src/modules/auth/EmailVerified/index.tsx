'use client';
import React from 'react';
import { Button, Card } from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
} from '../auth.styled';
import { useRouter } from 'next/navigation';
import {
  useAuthActionsContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import { isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { useIntl } from 'react-intl';
import type { User } from '@unpod/constants/types';

const EmailVerified = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { getAuthUser, getGlobalData } = useAuthActionsContext();
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onContinueCLick = () => {
    getAuthUser()
      .then((response) => {
        const typedResponse = response as { message?: string; data?: User };
        getGlobalData()
          .then(() => {
            infoViewActionsContext.showMessage(
              typedResponse.message || 'Success',
            );
            if (
              typedResponse?.data?.current_step === 'join_organization' ||
              typedResponse?.data?.current_step === 'organization'
            ) {
              if (isEmptyObject(typedResponse?.data?.organization || {})) {
                // router.push('/create-org');
                if (typedResponse?.data?.is_private_domain) {
                  router.push('/creating-identity/');
                } else {
                  router.push('/business-identity/');
                }
              } else {
                router.push('/join-org');
              }
            }
          })
          .catch(() => {
            router.push('/');
          });
      })
      .catch((response: { message?: string }) => {
        infoViewActionsContext.showError(response.message || 'Failed');
        router.push('/');
      });
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          <div className="text-center">
            <AppImage
              src={'/images/verified.gif'}
              alt="verified"
              width={240}
              height={240}
            />

            <StyledAuthTitle $mb={12}>
              {formatMessage({ id: 'emailVerified.title' })}
            </StyledAuthTitle>
            <StyledAuthContent type="secondary">
              {formatMessage({ id: 'emailVerified.subtitle' })}
            </StyledAuthContent>
          </div>

          <Button type="primary" onClick={onContinueCLick} block>
            {formatMessage({ id: 'common.continue' })}
          </Button>
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default EmailVerified;
