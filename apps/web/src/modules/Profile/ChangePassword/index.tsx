import React from 'react';
import { Button, Col, Form, Row } from 'antd';
import { AppGridContainer, AppPassword } from '@unpod/components/antd';
import { StyledRoot } from './index.styled';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { useIntl } from 'react-intl';
import { PASSWORD_REGX } from '@unpod/constants';

const { Item } = Form;

const ChangePassword = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const onSubmitSuccess = (formData: Record<string, unknown>) => {
    postDataApi('change-password/', infoViewActionsContext, formData)
      .then((response) => {
        const res = response as { message?: string };
        infoViewActionsContext.showMessage(res.message || 'Updated');
      })
      .catch((response) => {
        const res = response as { message?: string };
        infoViewActionsContext.showError(res.message || 'Error');
      });
  };

  return (
    <StyledRoot>
      <AppGridContainer>
        <Col sm={24}>
          <Form onFinish={onSubmitSuccess}>
            <AppGridContainer>
              <Col sm={24} md={12}>
                <Item
                  name="old_password"
                  rules={[
                    {
                      required: true,
                      message: formatMessage({
                        id: 'validation.enterOldPassword',
                      }),
                    },
                  ]}
                >
                  <AppPassword
                    placeholder={formatMessage({ id: 'form.oldPassword' })}
                  />
                </Item>

                <Item
                  name="new_password"
                  rules={[
                    {
                      required: true,
                      message: formatMessage({
                        id: 'validation.enterNewPassword',
                      }),
                    },
                    () => ({
                      validator(_, value) {
                        if (!value) {
                          return Promise.resolve();
                        }
                        if (!PASSWORD_REGX.test(value)) {
                          return Promise.reject(
                            formatMessage({
                              id: 'validation.passwordRequirements',
                            }),
                          );
                        }
                        return Promise.resolve();
                      },
                    }),
                  ]}
                >
                  <AppPassword
                    placeholder={formatMessage({ id: 'form.newPassword' })}
                  />
                </Item>

                <Item
                  name="repeat_password"
                  rules={[
                    {
                      required: true,
                      message: formatMessage({
                        id: 'validation.confirmPassword',
                      }),
                    },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('new_password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(
                          new Error(
                            formatMessage({
                              id: 'validation.passwordMismatch',
                            }),
                          ),
                        );
                      },
                    }),
                  ]}
                >
                  <AppPassword
                    placeholder={formatMessage({ id: 'form.confirmPassword' })}
                  />
                </Item>
              </Col>
            </AppGridContainer>

            <Row>
              <Button type="primary" htmlType="submit">
                {formatMessage({ id: 'common.updatePassword' })}
              </Button>
            </Row>
          </Form>
        </Col>
      </AppGridContainer>
    </StyledRoot>
  );
};

export default ChangePassword;
