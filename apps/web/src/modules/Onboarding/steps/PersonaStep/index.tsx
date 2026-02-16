'use client';
import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { Button, Flex, Form } from 'antd';
import { useIntl } from 'react-intl';
import { FooterBar } from '@/modules/Onboarding/index.styled';
import type { Pilot } from '@unpod/constants/types';

type PersonaStepProps = {
  agent: Pilot;
  updateAgentData: (
    formData: FormData,
    setLoading: React.Dispatch<React.SetStateAction<boolean>>,
    nextStep?: string,
  ) => void;
  setAgent: React.Dispatch<React.SetStateAction<Pilot>>;
  domainData?: {
    ai_agent?: {
      system_prompt?: string;
    };
  };
  setLoading?: React.Dispatch<React.SetStateAction<boolean>>;
};

type PersonaFormProps = {
  form: ReturnType<typeof Form.useForm>[0];
  agentData: Pilot;
  domainData?: PersonaStepProps['domainData'];
};

const PersonaForm = dynamic<PersonaFormProps>(
  () => import('@unpod/modules/AppIdentityAgentModule/Persona/PersonaForm'),
  { ssr: false },
);

const PersonaStep: React.FC<PersonaStepProps> = ({
  agent,
  updateAgentData,
  setAgent,
  domainData,
}) => {
  const { formatMessage } = useIntl();
  const [isLoading, setIsLoading] = useState(false);

  const [form] = Form.useForm();

  const onFinish = (values: Record<string, string>) => {
    const formData = new FormData();
    formData.append('name', agent.name || '');
    formData.append('handle', agent.handle || '');
    formData.append('greeting_message', 'Hello! How can I assist you today?');
    formData.append('system_prompt', values.system_prompt || '');
    formData.append(`conversation_tone`, values.conversation_tone || '');
    setAgent((prevAgent) => ({
      ...prevAgent,
      template: values.template,
    }));
    updateAgentData(formData, setIsLoading, '3');
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        ...agent,
        system_prompt: domainData?.ai_agent?.system_prompt || '',
      }}
      onFinish={onFinish}
    >
      <PersonaForm form={form} agentData={agent} domainData={domainData} />

      <FooterBar>
        <Flex justify="space-between" align="center">
          <Button
            type="primary"
            htmlType="submit"
            style={{ paddingLeft: 24, paddingRight: 24 }}
            loading={isLoading}
          >
            {formatMessage({ id: 'identityOnboarding.continue' })}
          </Button>
        </Flex>
      </FooterBar>
    </Form>
  );
};

export default PersonaStep;
