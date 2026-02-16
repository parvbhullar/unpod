'use client';
import React from 'react';
import { Button, Card, Form } from 'antd';
import AppPageLayout from '@unpod/components/common/AppPageLayout';
import { AppInput } from '@unpod/components/antd';
import { EMAIL_REGX } from '@unpod/constants';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';

import {
  StyledContactContainer,
  StyledContactContent,
  StyledContactHeader,
  StyledContactTitle,
} from './index.styled';

import { useRouter } from 'next/navigation';
import AppPhoneInput from '@unpod/components/antd/AppPhoneInput';
import { useIntl } from 'react-intl';

const { Item } = Form;

const ContactUs = () => {
  const [form] = Form.useForm();
  const router = useRouter();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { formatMessage } = useIntl();

  const onFinish = (payload: {
    name?: string;
    email?: string;
    phone?: { number?: string; countryCode?: string };
    message?: string;
  }) => {
    postDataApi('contacts/', infoViewActionsContext, {
      ...payload,
      business: 'default',
      products: ['Voice AI Infra'],
      phone: payload.phone?.number,
      phone_cc: payload.phone?.countryCode,
    })
      .then((data) => {
        infoViewActionsContext.showMessage(
          data.message || 'Submitted',
        );
        form.resetFields();
        setTimeout(() => {
          router.push('/');
        }, 1000);
      })
      .catch((error) => {
        infoViewActionsContext.showError(
          error.message || formatMessage({ id: 'contactUs.submitError' }),
        );
      });
  };

  return (
    <AppPageLayout layout="full">
      <StyledContactContainer>
        <Card>
          <StyledContactHeader>
            <StyledContactTitle level={3} $mb={4}>
              {formatMessage({ id: 'contactUs.title' })}
            </StyledContactTitle>
            <StyledContactContent type="secondary">
              {formatMessage({ id: 'contactUs.subtitle' })}
            </StyledContactContent>
          </StyledContactHeader>

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              business: 'default',
              products: ['Voice AI Infra'],
            }}
            size="large"
            onFinish={onFinish}
            autoComplete="off"
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
              <AppInput
                placeholder={formatMessage({ id: 'form.fullNameRequired' })}
              />
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
                placeholder={formatMessage({ id: 'form.emailRequired' })}
              />
            </Item>
            <Item
              name="phone"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.phoneError' }),
                },
              ]}
            >
              <AppPhoneInput />
            </Item>
            {/*<Item
              name="business"
              rules={[
                { required: true, message: 'Please enter your business name' },
              ]}
            >
              <AppInput placeholder="Business Name" />
            </Item>
            <Item name="products">
              <Checkbox.Group>
                <Row>
                  {services.map((service, index) => (
                    <Col xs={24} sm={12} key={index}>
                      <Space
                        style={{
                          marginBottom: 8,
                        }}
                      >
                        <Checkbox value={service}>
                          <span>{service}</span>
                        </Checkbox>
                      </Space>
                    </Col>
                  ))}
                </Row>
              </Checkbox.Group>
            </Item>*/}
            <Item style={{ marginTop: 24 }}>
              <Button
                type="primary"
                htmlType="submit"
                block
                size="large"
                loading={Boolean(
                  (infoViewActionsContext as { isLoading?: boolean }).isLoading,
                )}
              >
                {formatMessage({ id: 'contactUs.submit' })}
              </Button>
            </Item>
          </Form>
        </Card>
      </StyledContactContainer>
    </AppPageLayout>
  );
};

export default ContactUs;
