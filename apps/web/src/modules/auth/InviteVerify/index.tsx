'use client';
import React, { useEffect, useRef, useState } from 'react';
import { Button, Card } from 'antd';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
  StyledAvatar,
} from '../auth.styled';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  getDataApi,
  postDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import AppLoader from '@unpod/components/common/AppLoader';
import { MdClose } from 'react-icons/md';
import { useAppHistoryActions } from '@unpod/providers/AppHistoryProvider';
import { useIntl } from 'react-intl';
import type { Organization, Spaces } from '@unpod/constants/types';

const InviteVerify = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const verifyRef = useRef<InviteError | null>(null);
  const { isAuthenticated, isLoading } = useAuthContext();
  const { setRedirectTo, setHistoryOrg, setHistorySpace, setNextStep } =
    useAppHistoryActions();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [loading, setLoading] = useState(true);
  const { formatMessage } = useIntl();

  type Invitation = {
    is_verified?: boolean;
    invite_type?: string;
    organization?: Organization;
    space?: Spaces;
    user_exists?: boolean;
    user_email?: string;
  };

  type InviteError = {
    message?: string;
    invite_expired?: boolean;
    invite_token?: string;
    data?: Record<string, unknown>;
  };

  useEffect(() => {
    if (token && !isLoading) {
      postDataApi<Invitation>('core/invite/verify/', infoViewActionsContext, {
        token: token,
      })
        .then((response) => {
          // console.log('InviteVerify response.data: ', response.data);
          if (response.data) {
            goToNextPage(response.data);
          } else {
            setLoading(false);
          }
        })
        .catch((error) => {
          const payload = error as InviteError;
          console.log(payload.data);
          verifyRef.current = payload;
          infoViewActionsContext.showError(
            payload.message || 'Failed to verify',
          );
          setLoading(false);
        });
    } else if (!token) {
      setLoading(false);
    }
  }, [token, isLoading]);

  const goToNextPage = (invitation: Invitation) => {
    if (invitation.is_verified) {
      if (
        invitation.invite_type === 'organization' ||
        invitation.invite_type === 'join_organization'
      ) {
        setHistoryOrg(invitation.organization);
        setNextStep('join-org');
      } else if (
        invitation.invite_type === 'space' ||
        invitation.invite_type === 'join_space'
      ) {
        if (invitation.space) {
          setHistorySpace(invitation.space);
          setHistoryOrg(invitation.space.organization);
          setNextStep('join-space');
        }
      }

      if (invitation.user_exists) {
        if (isAuthenticated) {
          router.push('/join-org/');
        } else {
          setRedirectTo('/join-org/');
          router.push('/auth/signin/');
        }
      } else if (invitation.user_exists === false) {
        const email = invitation.user_email || '';
        router.push(`/auth/signup?email=${encodeURIComponent(email)}`);
      }
    }
  };

  const onResend = () => {
    const inviteToken = verifyRef.current?.invite_token;
    if (!inviteToken) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'invite.tokenExpired' }),
      );
      return;
    }
    getDataApi(`spaces/invite/resend/${inviteToken}/`, infoViewActionsContext)
      .then((response) => {
        const payload = response as { message?: string };
        infoViewActionsContext.showMessage(payload.message || 'Resent');
      })
      .catch((response) => {
        const payload = response as { message?: string };
        infoViewActionsContext.showError(payload.message || 'Failed to resend');
      });
  };

  return loading ? (
    <AppLoader />
  ) : (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          <div className="text-center">
            <StyledAvatar size={160} icon={<MdClose fontSize={80} />} />

            <StyledAuthTitle $mb={12}>
              {formatMessage({ id: 'invite.verifyFailed' })}
            </StyledAuthTitle>
            <StyledAuthContent type="danger">
              {verifyRef?.current?.message ||
                formatMessage({ id: 'invite.tokenExpired' })}
            </StyledAuthContent>
          </div>
          {verifyRef?.current?.invite_expired && (
            <Button type="primary" onClick={onResend} block>
              {formatMessage({ id: 'invite.verifyResend' })}
            </Button>
          )}
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default InviteVerify;
