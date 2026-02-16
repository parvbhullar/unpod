'use client';
import React, { useEffect, useState } from 'react';
import {
  getDataApi,
  postDataApi,
  useAuthActionsContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter, useSearchParams } from 'next/navigation';
import { getRandomColor } from '@unpod/helpers/StringHelper';
import {
  auth,
  googleAuthProvider,
  setAuthToken,
  setOrgHeader,
} from '@unpod/services';
import { useAppHistory } from '@unpod/providers/AppHistoryProvider';
import { consoleLog, isEmptyObject } from '@unpod/helpers/GlobalHelper';
import type { User } from '@unpod/constants/types';

import OTPVerification from '../OTPVerification';
import SignUpForm from './SignUpForm';
import { FlipCard, FlipContainer } from '../auth.styled';

const Signup = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {
    getGlobalData,
    signUpUser,
    updateAuthUser,
    storeToken,
    getSubscription,
  } = useAuthActionsContext();
  const { redirectTo } = useAppHistory();
  const searchParams = useSearchParams();
  const paramsEmail = searchParams.get('email');

  const router = useRouter();
  const [submitted, setSubmitted] = useState(false);
  const [email, setEmail] = useState(paramsEmail || '');

  useEffect(() => {
    if (paramsEmail) setEmail(paramsEmail || '');
  }, [paramsEmail]);

  const handleSignUpSuccess = (
    user: User & {
      current_step?: string;
      is_private_domain?: boolean;
      active_organization?: { domain_handle?: string };
    },
  ) => {
    if (redirectTo) {
      router.push(redirectTo);
    } else if (
      user.current_step === 'join_organization' ||
      user.current_step === 'organization'
    ) {
      if (isEmptyObject(user?.organization || {})) {
        // router.push('/create-org');
        if (user?.is_private_domain) {
          router.push('/creating-identity/');
        } else {
          router.push('/business-identity/');
        }
      } else {
        router.push('/join-org');
      }
    } else if (user?.current_step === 'space') {
      router.push('/create-space');
    } else if (user?.current_step === 'profile') {
      router.push('/basic-profile');
    } else if (user?.active_organization?.domain_handle) {
      router.push(`/org`);
    }
  };

  const onFormSubmit = (formPayload: {
    email: string;
    [key: string]: unknown;
  }) => {
    signUpUser({ ...formPayload, profile_color: getRandomColor() })
      .then((response) => {
        const responsePayload = response as {
          message?: string;
          data?: {
            token?: string;
            user?: User & {
              verification_done?: boolean;
              active_organization?: { domain_handle?: string };
            };
            verification_done?: boolean;
          };
        };
        // console.log('response.data: ', response.data);
        infoViewActionsContext.showMessage(responsePayload.message || '');

        if (responsePayload?.data?.token) {
          storeToken(responsePayload?.data?.token)
            .then(() => {
              if (responsePayload?.data?.token) {
                setAuthToken(responsePayload.data.token);
              }
              if (responsePayload?.data?.user) {
                updateAuthUser(responsePayload?.data?.user);
              }
              if (
                responsePayload?.data?.user?.active_organization?.domain_handle
              ) {
                setOrgHeader(
                  responsePayload?.data.user.active_organization.domain_handle,
                );
                getSubscription();
              }

              if (responsePayload?.data?.user) {
                handleSignUpSuccess(responsePayload?.data.user);
              }
            })
            .catch((response) => {
              const payload = response as { message?: string };
              infoViewActionsContext.showError(payload.message || '');
            });
        } else {
          if (responsePayload?.data?.verification_done) {
            router.push('/basic-profile');
          } else {
            setEmail(formPayload.email);
            setSubmitted(true);
          }
        }
      })
      .catch((response) => {
        const payload = response as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
      });
  };

  const onSignUpWithGoogle = () => {
    try {
      infoViewActionsContext.fetchStart();
      if (!auth || !googleAuthProvider) {
        infoViewActionsContext.fetchFinish();
        infoViewActionsContext.showError('Google auth is not configured');
        return;
      }
      auth.signInWithPopup(googleAuthProvider).then((data) => {
        const { credential } = data as {
          credential?: { idToken?: string; accessToken?: string };
        };
        const payload = {
          id_token: credential?.idToken,
          access_token: credential?.accessToken,
        };

        consoleLog('payload', payload);
        postDataApi<{ token?: string }>(
          'google/login/',
          infoViewActionsContext,
          payload,
        )
          .then((response) => {
            if (!response.data?.token) {
              infoViewActionsContext.showError('Missing token');
              return;
            }
            storeToken(response.data.token)
              .then(() => {
                if (response.data?.token) {
                  setAuthToken(response.data.token);
                }
                getDataApi<User>('auth/me/', infoViewActionsContext)
                  .then((data) => {
                    const apiPayload = data;
                    infoViewActionsContext.fetchFinish();
                    if (apiPayload.data?.active_organization?.domain_handle) {
                      setOrgHeader(
                        apiPayload.data.active_organization.domain_handle,
                      );
                      getSubscription();
                    }

                    if (apiPayload.data) {
                      updateAuthUser(apiPayload.data);
                    }

                    getGlobalData()
                      .then(() => {
                        if (apiPayload.data) {
                          handleSignUpSuccess(apiPayload.data);
                        }
                      })
                      .catch((response) => {
                        consoleLog('getGlobalData error', response);
                      });
                  })
                  .catch((error) => {
                    const payload = error as { message?: string };
                    infoViewActionsContext.fetchFinish();
                    infoViewActionsContext.showError(payload.message || '');
                  });
              })
              .catch((error) => {
                const payload = error as { message?: string };
                infoViewActionsContext.fetchFinish();
                infoViewActionsContext.showError(payload.message || '');
              });
          })
          .catch((error) => {
            const payload = error as { message?: string };
            infoViewActionsContext.fetchFinish();
            infoViewActionsContext.showError(payload.message || '');
          });
      });
    } catch (error) {
      console.error('error', error);
      infoViewActionsContext.fetchFinish();
      const payload = error as { message?: string };
      infoViewActionsContext.showError(payload.message || '');
    }
  };

  return (
    <FlipContainer>
      {submitted ? (
        <FlipCard $flipType="in">
          <OTPVerification email={email} setEmail={setEmail} />
        </FlipCard>
      ) : (
        <SignUpForm
          onFormSubmit={onFormSubmit}
          onSignUpWithGoogle={onSignUpWithGoogle}
          email={email}
        />
      )}
    </FlipContainer>
  );
};

export default Signup;
