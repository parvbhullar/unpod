import {useState} from 'react';
import {Button, Divider, Flex, Form} from 'antd';
import {SaveOutlined} from '@ant-design/icons';
import {useIntl} from 'react-intl';
import PersonaForm from './PersonaForm';
import {useAuthContext, useInfoViewContext} from '@unpod/providers';
import {StickyFooter, StyledTabRoot} from '../index.styled';
import {StyledMainContainer} from './index.styled';

const {useForm} = Form;

type PersonaProps = {
  agentData?: any;
  updateAgentData?: (
    data: FormData,
    setLoading?: (loading: boolean) => void,
  ) => void;
};

const Persona = ({agentData, updateAgentData}: PersonaProps) => {
  const {formatMessage} = useIntl();
  const [, setLoading] = useState(false);
  const [form] = useForm();
  const {activeOrg} = useAuthContext();
  const infoViewContext = useInfoViewContext();

  const handleFinish = (values: { system_prompt: string; tags?: string[] }) => {
    const formData = new FormData();
    formData.append('name', agentData?.name || '');
    formData.append('handle', agentData?.handle || '');
    formData.append(
      'greeting_message',
      formatMessage({id: 'identityOnboarding.defaultGreeting'}),
    );
    formData.append('system_prompt', values.system_prompt);
    formData.append('token', '250');
    formData.append(
      'chat_model',
      JSON.stringify({codename: 'gpt-4', provider: 7}),
    );
    formData.append(
      'embedding_model',
      JSON.stringify({codename: 'gpt-4', provider: 7}),
    );
    formData.append('temperature', '0.7');
    formData.append('provider', '7');
    (values.tags || []).forEach((tag: string, index: number) =>
      formData.append(`tags[${index}]`, tag),
    );

    updateAgentData?.(formData, setLoading);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{...agentData, tags: ['Friendly']}}
      onFinish={handleFinish}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <PersonaForm form={form} agentData={agentData}/>
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Divider/>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined/>}
            loading={infoViewContext?.loading}
            disabled={!activeOrg?.domain_handle}
          >
            {formatMessage({id: 'common.save'})}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default Persona;
