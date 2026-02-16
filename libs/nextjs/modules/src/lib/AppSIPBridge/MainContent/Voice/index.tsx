import { useState } from 'react';
import { Col, Form, Typography } from 'antd';
import { AppInput } from '@unpod/components/antd';
import { MdMic, MdOutlineVerifiedUser } from 'react-icons/md';
import { FaRobot } from 'react-icons/fa';
import { IoMdCall } from 'react-icons/io';

import {
  FormSection,
  FormTitle,
  ProviderCard,
  ProviderDesc,
  ProviderGrid,
  ProviderIconWrapper,
  ProviderTitle,
  StyledButton,
  StyledForm,
  SubText,
} from './index.styled';
import { useInfoViewActionsContext } from '@unpod/providers';

const PROVIDERS = [
  {
    key: 'LiveKit',
    icon: <MdMic size={32} />,
    desc: 'Real-time audio and video infrastructure',
  },
  {
    key: 'Vapi',
    icon: <FaRobot size={32} />,
    desc: 'Voice AI platform for conversational apps',
  },
  {
    key: 'Daily',
    icon: <IoMdCall size={32} />,
    desc: 'Video and audio APIs for developers',
  },
];

const Voice = () => {
  const [selectedProvider, setSelectedProvider] = useState('LiveKit');
  const [form] = Form.useForm();
  const infoViewActionsContext = useInfoViewActionsContext();

  const handleSubmit = () => {
    form
      .validateFields()
      .then((values) => {
        infoViewActionsContext.showMessage(
          'Credentials verified and connected!',
        );
        // handle connection logic here
      })
      .catch((info) => {
        infoViewActionsContext.showError('Please check your credentials.');
      });
  };

  return (
    <>
      <FormTitle>Voice Infrastructure Provider</FormTitle>
      <SubText>
        Select your Voice AI provider and configure the connection credentials.
      </SubText>
      <ProviderGrid gutter={16}>
        {PROVIDERS.map(({ key, icon, desc }) => (
          <Col span={8} key={key}>
            <ProviderCard
              hoverable
              isSelected={selectedProvider === key}
              onClick={() => setSelectedProvider(key)}
            >
              <ProviderIconWrapper>{icon}</ProviderIconWrapper>
              <ProviderTitle>{key}</ProviderTitle>
              <ProviderDesc>{desc}</ProviderDesc>
            </ProviderCard>
          </Col>
        ))}
      </ProviderGrid>

      <FormSection>
        <Typography.Title level={2}>
          Configure {selectedProvider} Credentials
        </Typography.Title>
        <StyledForm form={form} layout="vertical" requiredMark={true}>
          <Form.Item
            name="apiKey"
            rules={[{ required: true, message: 'Please enter your API key' }]}
          >
            <AppInput placeholder="Enter your API key" />
          </Form.Item>

          <Form.Item
            name="secret"
            rules={[{ required: true, message: 'Please enter your secret' }]}
          >
            <AppInput placeholder="Secret" />
          </Form.Item>

          <Form.Item
            name="sipUrl"
            rules={[
              { required: true, message: 'Please enter your SIP URL' },
              {
                pattern: /^sip:.+@.+$/,
                message:
                  'SIP URL must follow the format sip:example@domain.com',
              },
            ]}
          >
            <AppInput placeholder="SIP URL: sip:example@domain.com" />
          </Form.Item>

          <StyledButton type="button" onClick={handleSubmit}>
            <MdOutlineVerifiedUser style={{ marginRight: 6 }} />
            Verify and Connect
          </StyledButton>
        </StyledForm>
      </FormSection>
    </>
  );
};

export default Voice;
