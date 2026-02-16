import type { FocusEvent } from 'react';
import { Fragment, useState } from 'react';
import { Button, Flex, Form, message, Space, Tooltip } from 'antd';
import {
  MdAdd,
  MdDelete,
  MdOutlineClose,
  MdOutlineRecordVoiceOver,
  MdOutlineSettings,
} from 'react-icons/md';
import { useGetDataApi, useInfoViewContext } from '@unpod/providers';
import { AppDrawer, AppInput } from '@unpod/components/antd';
import { getMachineName } from '@unpod/helpers/StringHelper';
import { CollapseWrapper, StyledItemRow } from './index.styled';
import VoiceProfiles from './VoiceProfiles';
import VoiceProfileCard from './VoiceProfiles/VoiceProfileCard';
import CardWrapper from '@unpod/components/common/CardWrapper';
import {
  StickyFooter,
  StyledMainContainer,
  StyledTabRoot,
} from '../index.styled';
import { useIntl } from 'react-intl';
import { ConfigItem, Pilot, VoiceProfile } from '@unpod/constants/types';
import VoiceCollapseSection from './VoiceCollapseSection';
import { SaveOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd/es/form';

const { Item, List, useForm } = Form;

type VoiceFormProps = {
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
  headerForm?: FormInstance;
};

type AgentFormValues = Partial<VoiceProfile> & {
  transcriber_provider?: string;
  transcriber_language?: string;
  transcriber_model?: string;
  voice_provider?: string;
  voice_model?: string;
  quality?: string;
  config_items?: ConfigItem[];
  temperature?: number;
  max_tokens?: number;
  model?: string;
  provider?: string;
};

const VoiceForm = ({ agentData, updateAgentData }: VoiceFormProps) => {
  const infoViewContext = useInfoViewContext();
  const [form] = useForm();
  const { formatMessage } = useIntl();
  const [messageApi, contextHolder] = message.useMessage();
  const [openVoiceProfile, setOpenVoiceProfile] = useState(false);



  const [
    { apiData: voiceProfile, loading: selectedVoiceLoading },
    { setData },
  ] = useGetDataApi<VoiceProfile | null>(
    `/core/voice-profiles/${agentData?.telephony_config?.voice_profile_id}/`,
    { data: null },
    {},
    !!agentData?.telephony_config?.voice_profile_id,
  );

  console.log('agent data trancriber',agentData)
  const onFinish = (values: AgentFormValues) => {
    const formData: FormData = new FormData();

    const telephonyConfig = {
      transcriber: {
        provider: values.transcriber_provider || '',
        language: values.transcriber_language || '',
        model: values.transcriber_model || '',
      },
      voice: {
        provider: values.voice_provider || '',
        voice: values.voice || '',
        model: values.voice_model || '',
      },
      telephony: agentData?.telephony_config?.telephony,
      quality: values.quality || 'good',
      voice_profile_id: voiceProfile?.data?.agent_profile_id || null,
      config_items: values.config_items,
    };

    formData.append('temperature', String(values.temperature ?? ''));
    formData.append('token', String(values.max_tokens ?? ''));
    formData.append(
      'chat_model',
      JSON.stringify({ codename: values.model, provider: values?.provider }),
    );
    formData.append('provider', values.provider || '');
    formData.append(
      'embedding_model',
      JSON.stringify({ codename: values.model, provider: values?.provider }),
    );
    formData.append('name', agentData?.name || '');
    formData.append('telephony_config', JSON.stringify(telephonyConfig));
    formData.append('type', agentData?.type || '');
    formData.append('telephony_enabled', String(agentData?.type === 'Voice'));
    formData.append('name', agentData?.name || '');
    formData.append(
      'voice_temperature',
      String(values.voice_temperature ?? ''),
    );
    formData.append('voice_speed', String(values.voice_speed ?? ''));
    formData.append('voice_prompt', String(values.voice_prompt));
    updateAgentData?.(formData);
  };

  const onProfileSelect = (profile: VoiceProfile | null) => {
    setData({ data: profile });
    setOpenVoiceProfile(false);

    form.setFieldsValue({
      transcriber_provider: profile?.transcriber?.provider || '',
      voice_provider: profile?.voice?.provider || '',
      quality: profile?.quality || 'good',
      provider: profile?.chat_model?.provider || '',
      temperature: profile?.temperature || '',
      voice_prompt: profile?.voice_prompt || '',
    });

    setTimeout(() => {
      form.setFieldsValue({
        transcriber_model: profile?.transcriber?.model || '',
        transcriber_language:
          profile?.transcriber?.languages?.[0]?.code || 'en',
        voice_model: profile?.voice?.model || '',
        voice: profile?.voice?.voice || '',
        model: profile?.chat_model?.codename || '',
      });
    }, 300);
  };

  const onFinishFailed = ({ errorFields }: { errorFields: any[] }) => {
    if (!errorFields || errorFields.length === 0) return;
    messageApi.error(errorFields[0].errors[0]);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      initialValues={{
        transcriber_provider:
          agentData?.telephony_config?.transcriber?.provider || '',
        transcriber_language:
          agentData?.telephony_config?.transcriber?.language || '',
        transcriber_model:
          agentData?.telephony_config?.transcriber?.model || '',
        voice_provider: agentData?.telephony_config?.voice?.provider || '',
        voice_model: agentData?.telephony_config?.voice?.model || '',
        voice: agentData?.telephony_config?.voice?.voice || '',
        quality: agentData?.telephony_config?.quality || 'good',
        config_items: agentData?.telephony_config?.config_items,
        provider: agentData?.chat_model?.provider_info?.id || '',
        model: agentData?.chat_model?.codename || '',
        temperature: agentData?.temperature || 0.7,
        max_tokens: agentData?.token || 250,
        voice_speed: agentData?.voice_speed || 1.0,
        voice_temperature: agentData?.voice_temperature || 1.01,
        voice_prompt: agentData?.voice_prompt || '',
      }}
      onFinishFailed={onFinishFailed}
      preserve={true}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper
            title={formatMessage({ id: 'identityStudio.voiceProfile' })}
            icon={<MdOutlineRecordVoiceOver />}
            extra={
              voiceProfile?.data && (
                <Button
                  type="link"
                  size="small"
                  shape="round"
                  onClick={() => setOpenVoiceProfile(true)}
                >
                  {formatMessage({ id: 'identityStudio.manageProfiles' })}
                </Button>
              )
            }
          >
            {voiceProfile?.data ? (
              <VoiceProfileCard
                data={voiceProfile?.data}
                onProfileSelect={onProfileSelect}
                hideSelect
              />
            ) : (
              <Button
                shape="round"
                type="primary"
                size="small"
                loading={selectedVoiceLoading}
                onClick={() => setOpenVoiceProfile(true)}
                ghost
              >
                {formatMessage({ id: 'aiStudio.selectVoiceProfile' })}
              </Button>
            )}
          </CardWrapper>

          <CollapseWrapper>
            <VoiceCollapseSection
              form={form}
              agentData={agentData}
              voiceProfile={voiceProfile}
            />
          </CollapseWrapper>

          <CardWrapper
            title={formatMessage({ id: 'identityStudio.config' })}
            icon={<MdOutlineSettings />}
          >
            {/*<StyledLabel>Config</StyledLabel>*/}
            <List name="config_items">
              {(fields, { add, remove }) => (
                <Fragment>
                  {fields.map(({ key, name, ...restField }) => (
                    <StyledItemRow key={key}>
                      <Item
                        {...restField}
                        name={[name, 'config_key']}
                        rules={[
                          {
                            required: true,
                            message: formatMessage({
                              id: 'validation.fieldRequired',
                            }),
                          },
                        ]}
                      >
                        <AppInput
                          placeholder={formatMessage({
                            id: 'identityStudio.configKey',
                          })}
                          onBlur={(event: FocusEvent<HTMLInputElement>) => {
                            const configKey = event.target.value;

                            if (configKey) {
                              const formattedKey = getMachineName(configKey);
                              const items = form.getFieldValue('config_items');
                              items[name].config_key = formattedKey;
                              form.setFieldsValue({ config_items: items });
                            }
                          }}
                          asterisk
                        />
                      </Item>

                      <Item
                        {...restField}
                        name={[name, 'config_value']}
                        rules={[
                          {
                            required: true,
                            message: formatMessage({
                              id: 'validation.fieldRequired',
                            }),
                          },
                        ]}
                      >
                        <AppInput
                          placeholder={formatMessage({
                            id: 'identityStudio.configValue',
                          })}
                          asterisk
                        />
                      </Item>

                      <Item>
                        <Button
                          type="primary"
                          onClick={() => remove(name)}
                          icon={<MdDelete fontSize={18} />}
                          danger
                          ghost
                        />
                      </Item>
                    </StyledItemRow>
                  ))}

                  <Item>
                    <Button
                      type="dashed"
                      onClick={() => add()}
                      block
                      icon={<MdAdd />}
                    >
                      {formatMessage({
                        id: 'identityStudio.addField',
                      })}
                    </Button>
                  </Item>
                </Fragment>
              )}
            </List>
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={infoViewContext.loading}
          >
            Save
          </Button>
        </Flex>
      </StickyFooter>

      <AppDrawer
        title={formatMessage({ id: 'identityStudio.voiceProfiles' })}
        open={openVoiceProfile}
        onClose={() => setOpenVoiceProfile(false)}
        size={780}
        extra={
          <Space size={2}>
            <Tooltip title="Close">
              <Button
                type="text"
                size="small"
                shape="circle"
                icon={<MdOutlineClose fontSize={21} />}
                onClick={() => setOpenVoiceProfile(false)}
              />
            </Tooltip>
          </Space>
        }
      >
        <VoiceProfiles
          onProfileSelect={onProfileSelect}
          id={voiceProfile?.data?.agent_profile_id}
        />
      </AppDrawer>
      {contextHolder}
    </Form>
  );
};

export default VoiceForm;
