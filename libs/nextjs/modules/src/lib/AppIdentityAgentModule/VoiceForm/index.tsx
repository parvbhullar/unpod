import {type FocusEvent, Fragment, useEffect, useState} from 'react';
import {Button, Divider, Flex, Form, Radio, Select, Space, Tooltip,} from 'antd';
import {
  MdAdd,
  MdDelete,
  MdOutlineClose,
  MdOutlinePhoneEnabled,
  MdOutlineRecordVoiceOver,
  MdOutlineSettings,
} from 'react-icons/md';
import {ApiOutlined, AudioOutlined, GlobalOutlined, RobotOutlined, SaveOutlined,} from '@ant-design/icons';
import {useGetDataApi, useInfoViewContext} from '@unpod/providers';
import {AppDrawer, AppInput, AppSelect} from '@unpod/components/antd';
import {getMachineName} from '@unpod/helpers/StringHelper';
import {StyledItemRow, StyledMainContainer} from './index.styled';
import VoiceProfiles from '../../AppAgentModule/VoiceForm/VoiceProfiles';
import VoiceProfileCard from '../../AppAgentModule/VoiceForm/VoiceProfiles/VoiceProfileCard';
import CardWrapper from '@unpod/components/common/CardWrapper';
import {StickyFooter, StyledTabRoot} from '../index.styled';
import type {ProviderModel, VoiceProfile} from '@unpod/constants/types';

const {Item, List, useForm} = Form;
const {Option} = Select;
const {Group} = Radio;

type TelephonyNumber = {
  number: string;
  country?: string;
};

type VoiceFormValues = {
  phone_numbers?: string[];
  transcriber_provider?: string;
  transcriber_language?: string;
  transcriber_model?: string;
  voice_provider?: string;
  voice_model?: string;
  voice?: string;
  quality?: string;
  config_items?: { config_key?: string; config_value?: string }[];
};

type VoiceFormProps = {
  agentData?: any;
  updateAgentData?: (data: FormData) => void;
};

const VoiceForm = ({agentData, updateAgentData}: VoiceFormProps) => {
  const infoViewContext = useInfoViewContext();
  const [form] = useForm();
  const transcriberProviderId = Form.useWatch('transcriber_provider', form);
  const voiceProviderId = Form.useWatch('voice_provider', form);
  const transcriberModelId = Form.useWatch('transcriber_model', form);
  const voiceModelId = Form.useWatch('voice_model', form);
  const [openVoiceProfile, setOpenVoiceProfile] = useState(false);
  const [{apiData: telephonyNumbers}] = useGetDataApi(
    `core/telephony-numbers/?type=agent`,
    {
      data: [],
    },
  );
  const [
    {apiData: voiceProfile, loading: selectedVoiceLoading},
    {setData},
  ] = useGetDataApi<VoiceProfile | null>(
    `/core/voice-profiles/${agentData?.telephony_config?.voice_profile_id}/`,
    {data: null},
    {},
    !!agentData?.telephony_config?.voice_profile_id,
  );

  const [{apiData: providerTData, loading: providerTLoading}] = useGetDataApi<
    Array<{ id: number; name: string }>
  >(`core/providers/models/?model_type=TRANSCRIBER`, {
    data: [],
  });
  const [{apiData: providerVData, loading: providerVLoading}] = useGetDataApi<
    Array<{ id: number; name: string }>
  >(`core/providers/models/?model_type=VOICE`, {
    data: [],
  });

  const [
    {apiData: transcriberModelData, loading: transcriberLoading},
    {updateInitialUrl: updateTranscriberInitialUrl},
  ] = useGetDataApi<ProviderModel[]>(
    `core/providers/models/`,
    {
      data: [],
    },
    {},
    false,
  );
  const [
    {apiData: voiceModelData, loading: voiceLoading},
    {updateInitialUrl: updateVoiceInitialUrl},
  ] = useGetDataApi<ProviderModel[]>(
    `core/providers/models/`,
    {
      data: [],
    },
    {},
    false,
  );

  useEffect(() => {
    if (transcriberProviderId) {
      if (
        transcriberProviderId !==
        agentData?.telephony_config?.transcriber?.provider
      ) {
        form.setFieldValue('transcriber_model', '');
        form.setFieldValue('transcriber_language', '');
      }
      updateTranscriberInitialUrl(
        `core/providers/models/${transcriberProviderId}/`,
      );
    }
  }, [transcriberProviderId]);

  useEffect(() => {
    if (voiceProviderId) {
      if (voiceProviderId !== agentData?.telephony_config?.voice?.provider) {
        form.setFieldValue('voice_model', '');
        form.setFieldValue('voice', '');
      }
      updateVoiceInitialUrl(`core/providers/models/${voiceProviderId}/`);
    }
  }, [voiceProviderId]);

  const onFinish = (values: VoiceFormValues) => {
    const formData = new FormData();
    const telephonyNumberData = ((telephonyNumbers as any)?.data ??
      []) as TelephonyNumber[];
    const telephony = values?.phone_numbers?.map((number: string) => {
      return telephonyNumberData.find((item) => item.number === number);
    });

    const voiceProfileData = (voiceProfile as any)?.data as
      | VoiceProfile
      | undefined;
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
      telephony: telephony,
      quality: values.quality || 'good',
      voice_profile_id: voiceProfileData?.agent_profile_id || null,
      config_items: values.config_items,
    };

    formData.append('telephony_config', JSON.stringify(telephonyConfig));
    formData.append('type', agentData?.type ?? '');
    formData.append(
      'telephony_enabled',
      agentData?.type === 'Voice' ? 'true' : 'false',
    );
    formData.append('name', agentData?.name ?? '');
    updateAgentData?.(formData);
  };

  const onProfileSelect = (profile: any | null) => {
    if (!profile) {
      setOpenVoiceProfile(false);
      return;
    }
    setData({data: profile} as any);
    setOpenVoiceProfile(false);

    form.setFieldsValue({
      transcriber_provider: profile.transcriber?.provider || '',
      voice_provider: profile.voice?.provider || '',
      quality: profile.quality || 'good',
    });

    setTimeout(() => {
      form.setFieldsValue({
        transcriber_model: profile.transcriber?.model || '',
        transcriber_language: profile.transcriber?.language || '',
        voice_model: profile.voice?.model || '',
        voice: profile.voice?.voice || '',
      });
    }, 300);
  };

  const getTranscriberLanguage = () => {
    if (transcriberModelId)
      return transcriberModelData?.data?.find(
        (item) => item.slug === transcriberModelId,
      )?.languages;
    return [];
  };

  const getVoiceData = () => {
    if (voiceModelId)
      return voiceModelData?.data?.find((item) => item.slug === voiceModelId)
        ?.voices;
    return [];
  };

  const languageData = getTranscriberLanguage();
  const voiceData = getVoiceData();
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
        phone_numbers:
          (
            agentData?.telephony_config?.telephony as
              | TelephonyNumber[]
              | undefined
          )?.map((item) => item.number) || [],
        quality: agentData?.telephony_config?.quality || 'good',
        config_items: agentData?.telephony_config?.config_items,
      }}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper
            title="Voice Profile"
            icon={<MdOutlineRecordVoiceOver/>}
            extra={
              ((voiceProfile as any)?.data as VoiceProfile | undefined) && (
                <Button
                  type="link"
                  size="small"
                  shape="round"
                  onClick={() => setOpenVoiceProfile(true)}
                >
                  Manage Profiles
                </Button>
              )
            }
          >
            {((voiceProfile as any)?.data as VoiceProfile | undefined) ? (
              <VoiceProfileCard
                data={(voiceProfile as any)?.data}
                hideSelect
                onProfileSelect={onProfileSelect}
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
                Select
              </Button>
            )}
          </CardWrapper>

          <Item name="quality">
            <Group
              optionType="button"
              buttonStyle="solid"
              options={[
                {
                  label: 'Good Quality',
                  value: 'good',
                },
                {
                  label: 'High Quality',
                  value: 'high',
                },
              ]}
            />
          </Item>

          <>
            <Item
              hidden
              name="transcriber_provider"
              help="Service that will convert speech to text"
              rules={[
                {
                  required: true,
                  message: 'Please select a transcription provider',
                },
              ]}
            >
              <AppSelect
                placeholder="Transcription Provider"
                suffixIcon={<ApiOutlined/>}
                loading={providerTLoading}
              >
                {((providerTData as any)?.data ?? []).map(
                  (item: ProviderModel) => (
                    <Option
                      key={item.id ?? item.slug}
                      value={item.id ?? item.slug}
                    >
                      {item.name}
                    </Option>
                  ),
                )}
              </AppSelect>
            </Item>

            <Item
              hidden
              name="transcriber_model"
              help="Model that will process the transcription"
              rules={[
                {
                  required: true,
                  message: 'Please select a transcription model',
                },
              ]}
            >
              <AppSelect
                placeholder="Transcription model"
                suffixIcon={<RobotOutlined/>}
                loading={transcriberLoading}
                disabled={transcriberModelData?.data?.length === 0}
                // onChange={handleModelChange}
              >
                {((transcriberModelData as any)?.data ?? []).map(
                  (item: ProviderModel) => (
                    <Select.Option key={item.slug} value={item.slug}>
                      {item.name}
                    </Select.Option>
                  ),
                )}
              </AppSelect>
            </Item>

            <Item
              hidden
              name="transcriber_language"
              help="Language for speech recognition"
              rules={[{required: true, message: 'Please select a language'}]}
            >
              <AppSelect
                placeholder="Language for transcription"
                suffixIcon={<GlobalOutlined/>}
                loading={transcriberLoading}
                disabled={languageData?.length === 0}
              >
                {(languageData ?? []).map(
                  (item: { code: string; name: string }) => (
                    <Select.Option key={item.code} value={item.code}>
                      {item.name}
                    </Select.Option>
                  ),
                )}
              </AppSelect>
            </Item>
          </>

          <>
            <Item
              hidden
              name="voice_provider"
              help="Voice service provider"
              rules={[
                {required: true, message: 'Please select a voice provider'},
              ]}
            >
              <AppSelect
                placeholder="Voice Provider"
                suffixIcon={<ApiOutlined/>}
                loading={providerVLoading}
              >
                {((providerVData as any)?.data ?? []).map(
                  (item: ProviderModel) => (
                    <Select.Option
                      key={item.id ?? item.slug}
                      value={item.id ?? item.slug}
                    >
                      {item.name}
                    </Select.Option>
                  ),
                )}
              </AppSelect>
            </Item>

            <Item
              hidden
              name="voice_model"
              help="Model that will process the audio"
              rules={[
                {required: true, message: 'Please select a voice model'},
              ]}
            >
              <AppSelect
                placeholder="Voice model"
                suffixIcon={<RobotOutlined/>}
                loading={voiceLoading}
                disabled={voiceModelData?.data?.length === 0}
              >
                {((voiceModelData as any)?.data ?? []).map(
                  (item: ProviderModel) => (
                    <Select.Option key={item.slug} value={item.slug}>
                      {item.name}
                    </Select.Option>
                  ),
                )}
              </AppSelect>
            </Item>

            <Item
              hidden
              name="voice"
              help="Voice that will be used for text-to-speech"
              rules={[{required: true, message: 'Please select a voice'}]}
            >
              <AppSelect
                placeholder="Synthesized voice"
                suffixIcon={<AudioOutlined/>}
                disabled={voiceData?.length === 0}
              >
                {(voiceData ?? []).map((item) => (
                  <Select.Option key={item.code} value={item.code}>
                    {item.name}
                  </Select.Option>
                ))}
              </AppSelect>
            </Item>
          </>

          <CardWrapper icon={<MdOutlinePhoneEnabled/>} title="Telephony">
            <Item
              name="phone_numbers"
              help="Select a phone number for voice interactions"
              rules={[
                {required: true, message: 'Please select a phone number'},
              ]}
            >
              <AppSelect
                placeholder="Phone number for this agent"
                mode="multiple"
                suffixIcon={<MdOutlinePhoneEnabled fontSize={16}/>}
              >
                {(
                  ((telephonyNumbers as any)?.data ?? []) as TelephonyNumber[]
                ).map((item) => (
                  <Option key={item.number} value={item.number}>
                    {item.number} {item.country && `(${item.country})`}
                  </Option>
                ))}
              </AppSelect>
            </Item>
          </CardWrapper>

          <CardWrapper title="Config" icon={<MdOutlineSettings/>}>
            {/*<StyledLabel>Config</StyledLabel>*/}
            <List name="config_items">
              {(
                fields: any[],
                {
                  add,
                  remove,
                }: { add: () => void; remove: (index: number) => void },
              ) => (
                <Fragment>
                  {fields.map(({key, name, ...restField}) => (
                    <StyledItemRow key={key}>
                      <Item
                        {...restField}
                        name={[name, 'config_key']}
                        rules={[
                          {
                            required: true,
                            message: 'This field is required',
                          },
                        ]}
                      >
                        <AppInput
                          placeholder="Config Key"
                          onBlur={(event: FocusEvent<HTMLInputElement>) => {
                            const configKey = event.target.value;

                            if (configKey) {
                              const formattedKey = getMachineName(configKey);
                              const items =
                                (form.getFieldValue('config_items') as any[]) ||
                                [];
                              if (items[name]) {
                                items[name].config_key = formattedKey;
                              }
                              form.setFieldsValue({config_items: items});
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
                            message: 'This field is required',
                          },
                        ]}
                      >
                        <AppInput placeholder="Config Value" asterisk/>
                      </Item>

                      <Item>
                        <Button
                          type="primary"
                          onClick={() => remove(name)}
                          icon={<MdDelete fontSize={18}/>}
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
                      icon={<MdAdd/>}
                    >
                      Add field
                    </Button>
                  </Item>
                </Fragment>
              )}
            </List>
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Divider/>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined/>}
            loading={infoViewContext.loading}
          >
            Save
          </Button>
        </Flex>
      </StickyFooter>

      <AppDrawer
        title="Voice Profiles"
        open={openVoiceProfile}
        onClose={() => setOpenVoiceProfile(false)}
        width={780}
        extra={
          <Space size={2}>
            <Tooltip title="Close">
              <Button
                type="text"
                size="small"
                shape="circle"
                icon={<MdOutlineClose fontSize={21}/>}
                onClick={() => setOpenVoiceProfile(false)}
              />
            </Tooltip>
          </Space>
        }
      >
        <VoiceProfiles
          onProfileSelect={onProfileSelect}
          id={(voiceProfile as any)?.data?.agent_profile_id}
        />
      </AppDrawer>
    </Form>
  );
};

export default VoiceForm;
