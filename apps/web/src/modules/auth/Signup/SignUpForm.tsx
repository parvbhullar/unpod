import React from 'react';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import { AppInput, AppPassword } from '@unpod/components/antd';
import {
  StyledAuthContainer,
  StyledAuthContent,
  StyledAuthTitle,
  StyledHeader,
} from '../auth.styled';
import { Button, Card, Checkbox, Form, Typography } from 'antd';
import { FcGoogle } from 'react-icons/fc';
import { useRouter } from 'next/navigation';
import { EMAIL_REGX, PASSWORD_REGX } from '@unpod/constants';
import AppLink from '@unpod/components/next/AppLink';
import { useIntl } from 'react-intl';

const { Link, Paragraph, Text } = Typography;
const { Item } = Form;

type SignUpFormProps = {
  onFormSubmit: (values: {
    name: string;
    email: string;
    password: string;
    is_agree?: boolean;
  }) => void;
  onSignUpWithGoogle?: () => void;
  email?: string;
};

const SignUpForm = ({
  onFormSubmit,
  onSignUpWithGoogle,
  email = '',
}: SignUpFormProps) => {
  const router = useRouter();
  const { formatMessage } = useIntl();

  const onLoginClick = async () => {
    await router.push('/auth/signin');
  };

  return (
    <AppPageLayout layout="full">
      <StyledAuthContainer>
        <Card>
          <StyledHeader>
            <StyledAuthTitle level={3}>
              {formatMessage({ id: 'auth.createAccount' })}
            </StyledAuthTitle>

            <StyledAuthContent type="secondary">
              {formatMessage({ id: 'auth.accessWorkspace' })}
            </StyledAuthContent>

            <Button
              type="default"
              icon={<FcGoogle fontSize={21} />}
              onClick={onSignUpWithGoogle}
              block
              size="large"
            >
              {formatMessage({ id: 'auth.signUpWithGoogle' })}
            </Button>
          </StyledHeader>

          {/* <Divider>
            <Text type="secondary">OR</Text>
          </Divider> */}

          <Form
            autoComplete="off"
            onFinish={onFormSubmit}
            initialValues={{ email: email, is_agree: true }}
            layout="vertical"
            size="large"
          >
            <Item
              name="name"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.enterName' }),
                },
              ]}
            >
              <AppInput placeholder={formatMessage({ id: 'form.fullName' })} />
            </Item>
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
              extra={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {formatMessage({ id: 'auth.passwordHint' })}
                </Text>
              }
            >
              <AppPassword
                placeholder={formatMessage({ id: 'auth.password' })}
              />
            </Item>

            <Item
              name="is_agree"
              valuePropName="checked"
              rules={[
                {
                  validator: (_, value) =>
                    value
                      ? Promise.resolve()
                      : Promise.reject(
                          new Error(
                            formatMessage({ id: 'validation.acceptTerms' }),
                          ),
                        ),
                },
              ]}
            >
              <Checkbox>
                {formatMessage({ id: 'auth.acceptTerms' })}{' '}
                <AppLink href="/terms-and-conditions/">
                  {formatMessage({ id: 'auth.terms' })}{' '}
                </AppLink>
                {formatMessage({ id: 'auth.and' })}{' '}
                <AppLink href="/privacy-policy/">
                  {formatMessage({ id: 'auth.privacyPolicy' })}
                </AppLink>
              </Checkbox>
            </Item>

            <Item>
              <Button type="primary" htmlType="submit" block size="large">
                {formatMessage({ id: 'auth.signUp' })}
              </Button>
            </Item>

            <Paragraph type="secondary" className="text-center">
              {formatMessage({ id: 'auth.hasAccount' })}{' '}
              <Link onClick={onLoginClick} strong>
                {formatMessage({ id: 'auth.signIn' })}
              </Link>
            </Paragraph>
          </Form>
        </Card>
      </StyledAuthContainer>
    </AppPageLayout>
  );
};

export default React.memo(SignUpForm);
