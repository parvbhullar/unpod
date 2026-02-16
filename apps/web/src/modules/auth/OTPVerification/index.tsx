'use client';
import React, { useState } from 'react';
import { Button, Flex, Form, Input, Typography } from 'antd';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import {
  getDataApi,
  postDataApi,
  useAuthActionsContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { setAuthToken, setOrgHeader } from '@unpod/services';
import {
  StyledAction,
  StyledActionIcon,
  StyledActionWrapper,
  StyledButton,
  StyledCard,
  StyledContainer,
  StyledEmailContainer,
  StyledEmailText,
  StyledOTPContainer,
} from './index.styled';
import { useExpireTime } from '@unpod/custom-hooks';
import { FaRegEdit } from 'react-icons/fa';
import { AppInput } from '@unpod/components/antd';
import { EMAIL_REGX } from '@unpod/constants';
import { StyledAuthContainer } from '@/modules/auth/auth.styled';
import { useIntl } from 'react-intl';
import type { Organization, User } from '@unpod/constants/types';

const { Text } = Typography;
const { Item } = Form;

type OTPVerificationProps = {
  email: string;
  setEmail: (email: string) => void;
};

export default function OTPVerification({
  email,
  setEmail,
}: OTPVerificationProps) {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { storeToken, setActiveOrg, getSubscription, onSuccessAuthenticate } =
    useAuthActionsContext();
  const { formatMessage } = useIntl();

  const { remainingTime, resetTimer, minutes, seconds } = useExpireTime(120);

  const [otp, setOtp] = useState('');
  const [action, setAction] = useState<'verify' | 'resend' | 'skip' | null>(null);
  const [editableEmail, setEditableEmail] = useState(false);

  const onVerify = () => {
    setAction('verify');
    const payload = { email, otp };

    (
      postDataApi(
        '/auth/register/verify-otp/',
        infoViewActionsContext,
        payload,
        false,
      ) as Promise<{ message?: string; data?: { token?: string } }>
    )
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || '');

        const token = response.data?.token;
        if (!token) {
          infoViewActionsContext.showError('Invalid token');
          return;
        }

        storeToken(token)
          .then(() => {
            setAuthToken(token);
            (
              getDataApi('auth/me/', infoViewActionsContext) as Promise<{
                data?: User;
              }>
            )
              .then((data) => {
                const userData = data.data;
                if (userData?.active_organization?.domain_handle) {
                  setOrgHeader(userData.active_organization.domain_handle);
                  getSubscription();
                  setActiveOrg(userData.active_organization as Organization);
                }
                if (userData) {
                  onSuccessAuthenticate(userData);
                }
              })
              .catch((err) => {
                const payload = err as { message?: string };
                infoViewActionsContext.showError(payload.message || '');
              });
          })
          .catch((err) => {
            const payload = err as { message?: string };
            infoViewActionsContext.showError(payload.message || '');
          });
      })
      .catch((err) => {
        const payload = err as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
        setOtp('');
      })
      .finally(() => setAction(null));
  };

  const onResend = () => {
    setAction('resend');
    (
      postDataApi(
        '/auth/register/resend-otp/',
        infoViewActionsContext,
        { email },
        false,
      ) as Promise<{ message?: string }>
    )
      .then((res) => {
        infoViewActionsContext.showMessage(res.message || '');
        resetTimer();
      })
      .catch((err) => {
        const payload = err as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
      })
      .finally(() => setAction(null));
  };

  const onSkip = () => {
    setAction('skip');
    (
      postDataApi(
        '/auth/register/skip-otp/',
        infoViewActionsContext,
        { email },
        false,
      ) as Promise<{ message?: string; data?: { token?: string } }>
    )
      .then((response) => {
        infoViewActionsContext.showMessage(response.message || '');

        const token = response.data?.token;
        if (!token) {
          infoViewActionsContext.showError('Invalid token');
          return;
        }

        storeToken(token)
          .then(() => {
            setAuthToken(token);
            (
              getDataApi('auth/me/', infoViewActionsContext) as Promise<{
                data?: User;
              }>
            )
              .then((data) => {
                const userData = data.data;
                if (userData?.active_organization?.domain_handle) {
                  setOrgHeader(userData.active_organization.domain_handle);
                  getSubscription();
                  setActiveOrg(userData.active_organization as Organization);
                }
                if (userData) {
                  onSuccessAuthenticate(userData);
                }
              })
              .catch((err) => {
                const payload = err as { message?: string };
                infoViewActionsContext.showError(payload.message || '');
              });
          })
          .catch((err) => {
            const payload = err as { message?: string };
            infoViewActionsContext.showError(payload.message || '');
          });
      })
      .catch((err) => {
        const payload = err as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
      })
      .finally(() => setAction(null));
  };

  const onFinish = ({ email: newEmail }: { email: string }) => {
    (
      postDataApi(
        'auth/register/change-email/',
        infoViewActionsContext,
        { old_email: email, email: newEmail },
        false,
      ) as Promise<{ message?: string }>
    )
      .then((res) => {
        setEmail(newEmail);
        infoViewActionsContext.showMessage(res.message || '');
        setEditableEmail(false);
      })
      .catch((err) => {
        const payload = err as { message?: string };
        infoViewActionsContext.showError(payload.message || '');
      });
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <StyledCard>
          {editableEmail ? (
            <Text strong style={{ fontSize: 18 }}>
              {formatMessage({ id: 'auth.updateEmailTitle' })}
            </Text>
          ) : (
            <Text strong style={{ fontSize: 18 }}>
              {formatMessage({ id: 'auth.verificationTitle' })}
            </Text>
          )}

          {!editableEmail ? (
            <Text>{formatMessage({ id: 'auth.verificationSubtitle' })}</Text>
          ) : (
            <Text>{formatMessage({ id: 'auth.updateEmailSubTitle' })}</Text>
          )}

          {editableEmail ? (
            <Form
              onFinish={onFinish}
              key={email}
              initialValues={{ email: email }}
              style={{ width: '100%' }}
            >
              <StyledEmailContainer>
                <Item
                  style={{ width: '100%' }}
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
                    placeholder={formatMessage({ id: 'form.enterEmails' })}
                  />
                </Item>

                <StyledAction>
                  <Button htmlType="submit" type="primary" block>
                    {formatMessage({ id: 'common.update' })}
                  </Button>

                  <Button
                    block
                    type="default"
                    onClick={() => {
                      setEditableEmail(false);
                    }}
                  >
                    {formatMessage({ id: 'common.cancel' })}
                  </Button>
                </StyledAction>
              </StyledEmailContainer>
            </Form>
          ) : (
            <>
              <Form onFinish={onVerify}>
                <StyledContainer>
                  <StyledActionWrapper>
                    <StyledEmailText strong>{email}</StyledEmailText>

                    <StyledActionIcon
                      className="edit-btn"
                      onClick={() => setEditableEmail(true)}
                    >
                      <FaRegEdit size={16} />
                    </StyledActionIcon>
                  </StyledActionWrapper>

                  <Item
                    name="otp"
                    rules={[
                      {
                        required: true,
                        message: formatMessage({ id: 'validation.otp' }),
                      },
                    ]}
                  >
                    <StyledOTPContainer>
                      <Input.OTP
                        length={6}
                        size="large"
                        value={otp}
                        onChange={setOtp}
                      />
                    </StyledOTPContainer>
                  </Item>

                  <Flex
                    align="center"
                    gap={12}
                    style={{ width: '100%', marginTop: 6 }}
                  >
                    <Button
                      htmlType="submit"
                      type="primary"
                      block
                      loading={action === 'verify'}
                      disabled={action !== null || !otp}
                    >
                      {formatMessage({ id: 'auth.verify' })}
                    </Button>

                    <StyledButton
                      className={remainingTime <= 0 ? 'active' : ''}
                      block
                      type="default"
                      onClick={onResend}
                      loading={action === 'resend'}
                      disabled={remainingTime > 0 || action !== null}
                    >
                      {formatMessage({ id: 'auth.resend' })}
                    </StyledButton>
                  </Flex>

                  <Button
                    block
                    type="link"
                    onClick={onSkip}
                    loading={action === 'skip'}
                    disabled={action !== null}
                    style={{ marginTop: 4 }}
                  >
                    Skip Verification
                  </Button>
                </StyledContainer>
              </Form>

              {remainingTime > 0 && (
                <Text>
                  {formatMessage({ id: 'auth.resendIn' })} {minutes}:{seconds}{' '}
                  {formatMessage({ id: 'auth.minutes' })}
                </Text>
              )}
            </>
          )}
        </StyledCard>
      </StyledAuthContainer>
    </AppPageLayout>
  );
}
