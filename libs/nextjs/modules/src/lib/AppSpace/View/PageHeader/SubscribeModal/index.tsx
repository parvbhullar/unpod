import { Fragment, memo, useState } from 'react';
import { Button, Form, Input, Modal, Typography } from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import { postDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { EMAIL_REGX } from '@unpod/constants';
import {
  StyledContainer,
  StyledInfoWrapper,
  StylesImageWrapper,
} from './index.styled';
import AppLoader from '@unpod/components/common/AppLoader';
import { useIntl } from 'react-intl';

const { Paragraph, Title } = Typography;
const { Item, useForm } = Form;

const SubscribeModal = ({ currentSpace }: { currentSpace: any }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const { formatMessage } = useIntl();

  const [form] = useForm();

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
  };

  const onFormSubmit = (postData: any) => {
    setLoading(true);
    const payload = {
      email: postData.email,
      slug: currentSpace?.slug,
      invite_type: 'space',
    };

    postDataApi('core/invite/subscribe/', infoViewActionsContext, payload)
      .then((response: any) => {
        form.resetFields();
        setLoading(false);
        infoViewActionsContext.showMessage(response.message);
        handleCancel();
      })
      .catch((response: any) => {
        setLoading(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  return (
    <Fragment>
      <Button type="primary" size="small" shape="round" onClick={showModal}>
        {formatMessage({ id: 'common.subscribe' })}
      </Button>

      <Modal
        open={isModalOpen}
        onCancel={handleCancel}
        footer={null}
        closable={false}
      >
        <StyledContainer>
          <StylesImageWrapper>
            <AppImage
              src={
                currentSpace?.logo
                  ? `${currentSpace.logo}?tr=w-150,h-150`
                  : '/images/logo_avatar.png'
              }
              alt="logo"
              height={80}
              width={80}
              layout="fill"
              objectFit="cover"
            />
          </StylesImageWrapper>

          <StyledInfoWrapper>
            <Title level={2}>{currentSpace?.name}</Title>

            <Paragraph>
              {formatMessage({ id: 'subscribe.description' })}
            </Paragraph>
          </StyledInfoWrapper>

          <Form autoComplete="off" form={form} onFinish={onFormSubmit}>
            <Item
              name="email"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.enterEmail' }),
                },
                () => ({
                  validator(_rule, value: any) {
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
              <Input
                placeholder={formatMessage({ id: 'invite.enterEmails' })}
                size="large"
              />
            </Item>

            <Button type="primary" htmlType="submit" block>
              {formatMessage({ id: 'common.subscribe' })}
            </Button>
          </Form>
        </StyledContainer>
      </Modal>

      {loading ? <AppLoader /> : null}
    </Fragment>
  );
};

export default memo(SubscribeModal);
