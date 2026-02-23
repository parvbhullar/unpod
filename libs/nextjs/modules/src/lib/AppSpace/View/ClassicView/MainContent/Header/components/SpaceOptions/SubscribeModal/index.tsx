import {memo, useState} from 'react';
import {Button, Form, Input, Modal, Typography} from 'antd';
import AppImage from '@unpod/components/next/AppImage';
import {postDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {EMAIL_REGX} from '@unpod/constants';
import {StyledContainer, StyledInfoWrapper, StylesImageWrapper,} from './index.styled';
import AppLoader from '@unpod/components/common/AppLoader';

const {Paragraph, Title} = Typography;
const {Item, useForm} = Form;

type SubscribeModalProps = {
  type?: string;
  currentData?: { slug?: string; logo?: string; name?: string };
};

const SubscribeModal = ({
                          type = 'space',
                          currentData,
                        }: SubscribeModalProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const [form] = useForm();

  const showModal = () => {
    setIsModalOpen(true);
  };

  const handleCancel = () => {
    setIsModalOpen(false);
  };

  const onFormSubmit = (postData: { email?: string }) => {
    setLoading(true);
    const payload = {
      email: postData.email,
      slug: currentData?.slug,
      invite_type: type,
    };

    postDataApi('core/invite/subscribe/', infoViewActionsContext, payload)
      .then((response) => {
        form.resetFields();
        setLoading(false);
        const res = response as { message?: string };
        if (res.message) infoViewActionsContext.showMessage(res.message);
        handleCancel();
      })
      .catch((response) => {
        setLoading(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  const logoSrc =
    typeof currentData?.logo === 'string'
      ? `${currentData.logo}?tr=w-150,h-150`
      : '/images/logo_avatar.png';

  return (
    <>
      <Button type="primary" size="small" shape="round" onClick={showModal}>
        Subscribe
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
              src={logoSrc}
              alt="logo"
              height={80}
              width={80}
              layout="fill"
              objectFit="cover"
            />
          </StylesImageWrapper>

          <StyledInfoWrapper>
            <Title level={2}>{currentData?.name}</Title>

            <Paragraph>Please subscribe to access this space.</Paragraph>
          </StyledInfoWrapper>

          <Form autoComplete="off" form={form} onFinish={onFormSubmit}>
            <Item
              name="email"
              rules={[
                {
                  required: true,
                  message: 'Please enter your email!',
                },
                () => ({
                  validator(_, value) {
                    if (!value) {
                      return Promise.resolve();
                    }
                    if (!EMAIL_REGX.test(value)) {
                      return Promise.reject('Enter a valid email!');
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
            >
              <Input placeholder="Enter Email" size="large"/>
            </Item>

            <Button type="primary" htmlType="submit" block>
              Subscribe
            </Button>
          </Form>
        </StyledContainer>
      </Modal>

      {loading ? <AppLoader/> : null}
    </>
  );
};

export default memo(SubscribeModal);
