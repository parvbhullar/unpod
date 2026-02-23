'use client';
import {Fragment, useState} from 'react';
import {Button, Flex, Form, type FormInstance, Modal, Typography} from 'antd';
import ToneCardList from './ToneCardList';
import {postDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {
  CardWrapper,
  StyledFlex,
  StyledInputWrapper,
  StyledItemWrapper,
  StyledText,
  StyledTextArea,
  Tip,
  TipText,
} from './index.styled';
import Template from './Template';
import {FaRegStar} from 'react-icons/fa6';
import {RxDashboard} from 'react-icons/rx';
import {useIntl} from 'react-intl';

const {Text} = Typography;
const {Item} = Form;

export const tonePersonality = [
  {
    key: 'Professional',
    label: 'aiStudio.professional',
    icon: '💼',
  },
  {key: 'Friendly', label: 'aiStudio.friendly', icon: '😊'},
  {key: 'Casual', label: 'aiStudio.casual', icon: '🎯'},
  {
    key: 'Empathetic',
    label: 'aiStudio.empathetic',
    icon: '💜',
  },
];

type PersonaFormProps = {
  form: FormInstance;
  agentData?: any;
  domainData?: Record<string, unknown>;
};

const PersonaForm = ({form, agentData, domainData}: PersonaFormProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {activeOrg} = useAuthContext();
  const {formatMessage} = useIntl();
  const [isOpen, setIsOpen] = useState(false);
  const systemPromptValue = Form.useWatch('system_prompt', form);
  const selectedTemplate = form.getFieldValue('template');
  const characterCount = systemPromptValue?.length || 0;
  const [loading, setLoading] = useState(false);

  const identity_payload = {
    identity_name: agentData?.name,
    description: agentData?.description,
    purpose: agentData?.purpose,
    tags: agentData?.tags,
    org_name: activeOrg?.name,
  };

  const onGenerateScript = () => {
    setLoading(true);
    const payload = {
      data: domainData ? domainData : identity_payload,
      template: form.getFieldValue('template')?.slug,
      conversation_tone: form.getFieldValue('conversation_tone'),
      system_prompt: form.getFieldValue('system_prompt'),
    };

    postDataApi('/core/generate-ai-persona/', infoViewActionsContext, payload)
      .then((response: any) => {
        const generated =
          response?.data?.system_prompt || 'Script could not be generated';

        form.setFieldsValue({system_prompt: generated});
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      })
      .finally(() => setLoading(false));
  };

  return (
    <Fragment>
      <Item
        name="conversation_tone"
        rules={[
          {
            required: true,
            message: formatMessage({id: 'validation.purpose'}),
          },
        ]}
      >
        <ToneCardList
          items={tonePersonality}
          label={formatMessage({id: 'aiStudio.sectionLabel'})}
        />
      </Item>

      <StyledInputWrapper>
        <StyledItemWrapper>
          <Text strong>
            {formatMessage({id: 'identityStudio.behaviorInstructions'})}
          </Text>
        </StyledItemWrapper>

        <CardWrapper
          actions={[
            <Flex justify="space-between" gap={10} align="center">
              <StyledText>
                {`${characterCount} ${formatMessage({id: 'aiStudio.characters'})}`}
              </StyledText>

              <StyledFlex justify="flex-end" gap={10}>
                <Button
                  onClick={() => setIsOpen(true)}
                  icon={<RxDashboard size={14}/>}
                >
                  {selectedTemplate?.name
                    ? selectedTemplate?.name
                    : `${formatMessage({id: 'aiStudio.chooseTemplate'})}`}
                </Button>

                <Button
                  type="primary"
                  onClick={() => onGenerateScript()}
                  icon={<FaRegStar size={16}/>}
                  loading={loading}
                >
                  {formatMessage({id: 'aiStudio.generateButton'})}
                </Button>
              </StyledFlex>
            </Flex>,
          ]}
        >
          <Item
            name="system_prompt"
            rules={[
              {
                required: true,
                message: formatMessage({id: 'aiStudio.systemPromptError'}),
              },
            ]}
          >
            <StyledTextArea
              placeholder={formatMessage({
                id: 'aiStudio.systemPromptPlaceholder',
              })}
              autoSize={{minRows: 4, maxRows: 8}}
            />
          </Item>
        </CardWrapper>

        <Tip>
          <span>💡</span>
          <TipText>{formatMessage({id: 'aiStudio.tip'})}</TipText>
        </Tip>
      </StyledInputWrapper>

      <Modal
        title={formatMessage({id: 'aiStudio.templateModelTitle'})}
        open={isOpen}
        onCancel={() => setIsOpen(false)}
        footer={null}
        centered
        width={630}
      >
        <Template form={form} setIsOpen={setIsOpen}/>
      </Modal>
    </Fragment>
  );
};

export default PersonaForm;
