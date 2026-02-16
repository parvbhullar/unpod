'use client';
import React, { useState } from 'react';
import AppLink from '@unpod/components/next/AppLink';
import { useRouter } from 'next/navigation';
import { Button, Card, Checkbox, Form, Row, Typography } from 'antd';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import { AppInput, AppPassword } from '@unpod/components/antd';
import {
  postDataApi,
  useAuthActionsContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { consoleLog, isEmptyObject } from '@unpod/helpers/GlobalHelper';
import { EMAIL_REGX, PASSWORD_REGX } from '@unpod/constants';
import { useAppHistory } from '@unpod/providers/AppHistoryProvider';
import useIsDesktop from '@unpod/custom-hooks/useIsDesktop';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
  StyledContentWrapper,
  StyledHeader,
} from '../auth.styled';
import { useIntl } from 'react-intl';
import type { User } from '@unpod/constants/types';

const { Paragraph } = Typography;
const { Item } = Form;

type SignInFormProps = {
  setEmail: (email: string) => void;
  setVerifyEmail: (value: boolean) => void;
  email?: string;
};

type SignInResponse = {
  data?: User & {
    current_step?: string;
    is_private_domain?: boolean;
    active_space?: { slug?: string };
    organization?: Record<string, unknown>;
  };
};

const SignInForm = ({ setEmail, setVerifyEmail, email }: SignInFormProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { redirectTo } = useAppHistory();
  const { signInUser, getGlobalData } = useAuthActionsContext();
  const router = useRouter();
  const { isDesktopApp } = useIsDesktop();
  const { formatMessage } = useIntl();

  const [verificationOtpSent, setVerificationOtpSent] = useState(false);

  const handleSignInSuccess = (response: SignInResponse) => {
    getGlobalData()
      .then(() => {
        if (redirectTo) {
          router.push(redirectTo);
        } else if (
          response?.data?.current_step === 'join_organization' ||
          response?.data?.current_step === 'organization'
        ) {
          if (isEmptyObject(response?.data?.organization || {})) {
            // router.push('/create-org');
            if (response?.data?.is_private_domain) {
              router.push('/creating-identity/');
            } else {
              router.push('/business-identity/');
            }
          } else {
            router.push('/join-org');
          }
        } else if (response?.data?.current_step === 'space') {
          router.push('/create-space');
        } else if (response?.data?.current_step === 'profile') {
          router.push('/basic-profile');
        } else {
          if (
            process.env.productId === 'unpod.ai' &&
            response?.data?.active_space?.slug
          ) {
            router.replace(
              `/spaces/${response?.data?.active_space.slug}/call/`,
            );
          } else {
            router.push(`/org`);
          }
        }
      })
      .catch((response: { message?: string }) => {
        consoleLog('getGlobalData error', response);
      });
  };

  const onFinish = (payload: { email: string; password: string }) => {
    setEmail(payload.email);

    signInUser(payload)
      .then((response) => {
        handleSignInSuccess(response as SignInResponse);
      })
      .catch((response) => {
        const payload = response as {
          message?: string;
          email_verified?: boolean | 'false';
        };
        infoViewActionsContext.showError(payload.message || '');
        if (
          payload?.email_verified === 'false' ||
          payload?.email_verified === false
        ) {
          setVerificationOtpSent(true);
        }
      });
  };

  /*const signInUserWithGoogle = () => {
    try {
      infoViewActionsContext.fetchStart();
      auth
        .signInWithPopup(googleAuthProvider)
        .then((data) => {
          const { credential } = data;
          const payload = {
            id_token: credential?.idToken,
            access_token: credential?.accessToken,
          };

          consoleLog('payload', payload);
          postDataApi('google/login/', infoViewActionsContext, payload)
            .then((response) => {
              storeToken(response?.token)
                .then(() => {
                  setAuthToken(response.token);
                  getDataApi('auth/me/', infoViewActionsContext)
                    .then((data) => {
                      infoViewActionsContext.fetchFinish();

                      if (data.data?.active_organization) {
                        setOrgHeader(
                          data.data.active_organization.domain_handle,
                        );
                        getSubscription();
                      }

                      updateAuthUser(data.data);
                      handleSignInSuccess(data);
                    })
                    .catch((error) => {
                      infoViewActionsContext.fetchFinish();
                      infoViewActionsContext.showError(error.message);
                    });
                })
                .catch((error) => {
                  infoViewActionsContext.fetchFinish();
                  infoViewActionsContext.showError(error.message);
                });
            })
            .catch((error) => {
              infoViewActionsContext.fetchFinish();
              infoViewActionsContext.showError(error.message);
            });
        })
        .catch((error) => {
          infoViewActionsContext.fetchFinish();
          infoViewActionsContext.showError(error.message);
        });
    } catch (error) {
      infoViewActionsContext.fetchFinish();
      infoViewActionsContext.showError(error.message);
    }
  };*/

  /*const onResendVerificationLink = () => {
    postDataApi('resend-verification/', infoViewActionsContext, {
      email: email,
    })
      .then((response) => {
        infoViewActionsContext.showMessage(response.message);
        setVerificationLinkSent(true);
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };*/

  const onEmailVerifyClick = () => {
    setVerifyEmail(true);
    postDataApi(
      '/auth/register/resend-otp/',
      infoViewActionsContext,
      { email },
      false,
    )
      .then((res) => {
        const payload = res as { message?: string };
        infoViewActionsContext.showMessage(payload.message || '');
      })
      .catch((err) => {
        const payload = err as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
      });
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          <StyledHeader>
            <StyledAuthTitle level={3} $mb={4}>
              {formatMessage({ id: 'auth.signInToContinue' })}
            </StyledAuthTitle>
            {verificationOtpSent && (
              <StyledContentWrapper>
                <StyledAuthContent type="danger">
                  {formatMessage({ id: 'auth.emailNotVerified' })}
                </StyledAuthContent>
                <Button type="link" onClick={onEmailVerifyClick}>
                  {formatMessage({ id: 'auth.verifyEmail' })}
                </Button>
              </StyledContentWrapper>
            )}

            {/*<Button
              type="default"
              icon={<FcGoogle fontSize={21} />}
              onClick={signInUserWithGoogle}
              block
              size="large"
            >
              Sign in with Google
            </Button>*/}
          </StyledHeader>

          {/* <Divider>
            <Text type="secondary">OR</Text>
          </Divider> */}

          <Form
            autoComplete="off"
            initialValues={{ remember: true }}
            onFinish={onFinish}
            layout="vertical"
            size="large"
          >
            <Item
              name="email"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.enterEmail' }),
                },
                () => ({
                  validator(_, value) {
                    if (!value) {
                      return Promise.resolve();
                    }
                    if (!EMAIL_REGX.test(value)) {
                      return Promise.reject(
                        formatMessage({ id: 'validation.validEmail' }),
                      );
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
            >
              <AppInput
                placeholder={formatMessage({ id: 'form.emailAddress' })}
              />
            </Item>

            <Item
              name="password"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.enterPassword' }),
                },
                () => ({
                  validator(_, value) {
                    if (!value) {
                      return Promise.resolve();
                    }
                    if (!PASSWORD_REGX.test(value)) {
                      return Promise.reject(
                        formatMessage({ id: 'validation.validPassword' }),
                      );
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
            >
              <AppPassword
                placeholder={formatMessage({ id: 'auth.password' })}
              />
            </Item>

            <Row justify="space-between" wrap>
              <Item name="remember" valuePropName="checked">
                <Checkbox>{formatMessage({ id: 'auth.rememberMe' })}</Checkbox>
              </Item>

              <Item>
                <AppLink href="/auth/forgot-password">
                  {formatMessage({ id: 'auth.forgotPassword' })}
                </AppLink>
              </Item>
            </Row>

            <Item>
              <Button type="primary" htmlType="submit" block size="large">
                {formatMessage({ id: 'auth.signIn' })}
              </Button>
            </Item>

            {isDesktopApp && (
              <Paragraph type="secondary" className="text-center">
                {formatMessage({ id: 'auth.noAccount' })}
                <AppLink href="/auth/signup">
                  {formatMessage({ id: 'auth.signUp' })}
                </AppLink>
              </Paragraph>
            )}
          </Form>
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default SignInForm;
