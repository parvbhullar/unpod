import React, {Fragment, useEffect} from 'react';
import type {CollapseProps, FormInstance} from 'antd';
import {Checkbox, Collapse, Flex, Form, Space, Typography} from 'antd';
import {
  ApiOutlined,
  AudioOutlined,
  GlobalOutlined,
  InfoCircleOutlined,
  RobotOutlined,
  TrademarkOutlined,
} from '@ant-design/icons';
import {TbPlugConnected} from 'react-icons/tb';
import {AiOutlineApi} from 'react-icons/ai';
import {RiVoiceprintLine} from 'react-icons/ri';
import {AppInput, AppInputNumber, AppSelect} from '@unpod/components/antd';
import TemperatureSlider from '../ModelForm/TemperatureSlider';
import {StyledCollapseItemRow, StyledModelOption} from './index.styled';
import AppTextArea from '@unpod/components/antd/AppTextArea';
import {useIntl} from 'react-intl';
import {Pilot, ProviderModel, ProviderModelVoice, VoiceProfile, VoiceProfileLanguage,} from '@unpod/constants/types';
import {useGetDataApi} from '@unpod/providers';

const {Text} = Typography;
const {Item} = Form;

type VoiceCollapseSectionProps = {
  form: FormInstance;
  agentData: Pilot;
  voiceProfile: VoiceProfile;
};

const VoiceCollapseSection: React.FC<VoiceCollapseSectionProps> = ({
                                                                     agentData,
                                                                     form,
                                                                     voiceProfile,
                                                                   }) => {
  const {formatMessage} = useIntl();

  const llmProvider = Form.useWatch('provider', form);
  const llmModel = Form.useWatch('model', form);
  const transcriberProviderId = Form.useWatch('transcriber_provider', form);
  const voiceProviderId = Form.useWatch('voice_provider', form);
  const transcriberModelId = Form.useWatch('transcriber_model', form);
  const voiceModelId = Form.useWatch('voice_model', form);
  const manualVoiceEnabled = Form.useWatch('manualVoiceId', form);

  const [{apiData: modalProviderData, loading: providerLoading}] =
    useGetDataApi<ProviderModel[]>(`core/providers/models/?model_type=LLM`, {
      data: [],
    });

  const [{apiData: providerTData, loading: providerTLoading}] = useGetDataApi<
    ProviderModel[]
  >(`core/providers/models/?model_type=TRANSCRIBER`, {
    data: [],
  });

  const [{apiData: providerVData, loading: providerVLoading}] = useGetDataApi<
    ProviderModel[]
  >(`core/providers/models/?model_type=VOICE`, {
    data: [],
  });

  const [
    {apiData: llmModelData, loading: llmLoading},
    {updateInitialUrl: updateLLMInitialUrl},
  ] = useGetDataApi<ProviderModel[]>(
    `core/providers/models/`,
    {
      data: [],
    },
    {},
    false,
  );

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
    if (llmProvider) {
      if (llmProvider !== agentData?.chat_model?.provider_info?.id) {
        form.setFieldValue('model', '');
      }
      updateLLMInitialUrl(
        `core/providers/models/${llmProvider}/?model_type=LLM`,
      );
    }
  }, [llmProvider]);

  useEffect(() => {
    if (llmModel) {
      const llmModelObj = llmModelData?.data?.find(
        (item) => item.codename === llmModel,
      );
      if (llmModelObj?.realtime_sts) {
        const llmProviderObj = providerVData?.data?.find(
          (item: ProviderModel) => item.id === llmProvider,
        );

        if (llmProviderObj) {
          form.setFieldsValue({
            voice_provider: llmProvider,
            voice_model: llmModel,
          });

          updateVoiceInitialUrl(
            `core/providers/models/${llmProvider}/?model_type=TTS`,
          );
        }
      }
    }
  }, [llmModel]);

  useEffect(() => {
    if (transcriberProviderId) {
      updateTranscriberInitialUrl(
        `core/providers/models/${transcriberProviderId}/?model_type=STT`,
      );
    }
  }, [transcriberProviderId]);

  useEffect(() => {
    if (voiceProviderId) {
      updateVoiceInitialUrl(
        `core/providers/models/${voiceProviderId}/?model_type=TTS`,
      );
    }
  }, [voiceProviderId]);

  useEffect(() => {
    if (
      voiceProfile?.data &&
      transcriberModelData?.data?.length &&
      voiceModelData?.data?.length
    ) {
      const profile: VoiceProfile = voiceProfile?.data as VoiceProfile;

      form.setFieldsValue({
        transcriber_model: profile?.transcriber?.model,
        transcriber_language: profile?.transcriber?.languages?.[0]?.code,
        voice_model: profile?.voice?.model,
        voice: profile?.voice?.voice,
        model: profile?.chat_model?.codename,
      });
    }
  }, [transcriberModelData, voiceModelData, voiceProfile]);

  const getTranscriberLanguage = () => {
    if (transcriberModelId)
      return transcriberModelData?.data?.find(
        (item) => item.codename === transcriberModelId,
      )?.languages;
    return [];
  };

  const getVoiceData = () => {
    if (voiceModelId)
      return voiceModelData?.data?.find(
        (item) => item.codename === voiceModelId,
      )?.voices;
    return [];
  };

  const onVoiceProviderChange = () => {
    form.setFieldsValue({voice_model: '', voice: ''});
  };

  const onVoiceModelChange = () => {
    form.setFieldsValue({voice: ''});
  };

  const languageData = getTranscriberLanguage();
  const voiceData = getVoiceData();

  const items: CollapseProps['items'] = [
    {
      key: '1',
      label: (
        <Flex align="center" gap={8}>
          <TbPlugConnected size={18}/>
          <Text strong>{formatMessage({id: 'identityStudio.model'})}</Text>
        </Flex>
      ),
      children: (
        <Fragment>
          <Item
            name="provider"
            help={formatMessage({
              id: 'identityStudio.selectProvider',
            })}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.providerPlaceholder',
              })}
              loading={providerLoading}
              suffixIcon={<ApiOutlined/>}
              options={modalProviderData?.data?.map((p: ProviderModel) => ({
                kay: p.id,
                value: p.id,
                label: p.name,
              }))}
            />
          </Item>
          <Item
            name="model"
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.modelMassage',
                }),
              },
            ]}
            help={formatMessage({id: 'identityStudio.modelHelp'})}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.modelPlaceholder',
              })}
              suffixIcon={<RobotOutlined/>}
              loading={llmLoading}
              disabled={!llmProvider}
              options={llmModelData?.data?.map(
                (item: ProviderModel, index: number) => ({
                  key: index,
                  value: item.codename,
                  label: (
                    <StyledModelOption>
                      <Text>{item.name}</Text>
                      <Space>
                        {item.inference && (
                          <Text title="Available on low latency inference">
                            <InfoCircleOutlined/>
                          </Text>
                        )}
                        {item.realtime_sts && (
                          <Text title="This is Realtime(STS) model">
                            <TrademarkOutlined/>
                          </Text>
                        )}
                      </Space>
                    </StyledModelOption>
                  ),
                }),
              )}
            />
          </Item>

          <Item
            name="max_tokens"
            help={formatMessage({id: 'identityStudio.maxTokensHelp'})}
          >
            <AppInputNumber
              placeholder={formatMessage({
                id: 'identityStudio.maxTokensPlaceholder',
              })}
            />
          </Item>

          <Item
            name="temperature"
            help={formatMessage({
              id: 'identityStudio.temperatureHelp',
            })}
          >
            <TemperatureSlider/>
          </Item>
        </Fragment>
      ),
      forceRender: true,
    },

    {
      key: '2',
      label: (
        <Flex align="center" gap={8}>
          <AiOutlineApi size={18}/>
          <Text strong>
            {formatMessage({id: 'identityStudio.transcriberTitle'})}
          </Text>
        </Flex>
      ),
      children: (
        <Fragment>
          <Item
            name="transcriber_provider"
            help={formatMessage({
              id: 'identityStudio.transcriptionProviderDesc',
            })}
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.transcriptionProvider',
                }),
              },
            ]}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.transcriptionProvider',
              })}
              suffixIcon={<ApiOutlined/>}
              loading={providerTLoading}
              options={providerTData?.data?.map((item: ProviderModel) => ({
                key: item.id,
                value: item.id,
                label: item.name,
              }))}
            />
          </Item>
          <Item
            name="transcriber_model"
            help={formatMessage({
              id: 'identityStudio.transcriptionModelDesc',
            })}
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.transcriptionModel',
                }),
              },
            ]}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.transcriptionModel',
              })}
              suffixIcon={<RobotOutlined/>}
              loading={transcriberLoading}
              disabled={transcriberModelData?.data?.length === 0}
              options={transcriberModelData?.data?.map(
                (item: ProviderModel, index: number) => ({
                  key: index,
                  value: item.codename,
                  label: (
                    <StyledModelOption>
                      <Text>{item.name}</Text>
                      <Space>
                        {item.inference && (
                          <Text title="Available on low latency inference">
                            <InfoCircleOutlined/>
                          </Text>
                        )}
                        {item.realtime_sts && (
                          <Text title="This is Realtime(STS) model">
                            <TrademarkOutlined/>
                          </Text>
                        )}
                      </Space>
                    </StyledModelOption>
                  ),
                }),
              )}
            />
          </Item>
          <Item
            name="transcriber_language"
            help={formatMessage({id: 'identityStudio.languageDesc'})}
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.language',
                }),
              },
            ]}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.languageForTranscription',
              })}
              suffixIcon={<GlobalOutlined/>}
              loading={transcriberLoading}
              disabled={languageData?.length === 0}
              options={languageData?.map((item: VoiceProfileLanguage) => ({
                key: item.code,
                value: item.code,
                label: item.name,
              }))}
            />
          </Item>
        </Fragment>
      ),
      forceRender: true,
    },

    {
      key: '3',
      label: (
        <Flex align="center" gap={8}>
          <RiVoiceprintLine/>
          <Text strong>{formatMessage({id: 'voiceConfig.title'})}</Text>
        </Flex>
      ),
      children: (
        <Fragment>
          <Item
            name="voice_provider"
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.voiceProvider',
                }),
              },
            ]}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.voiceProvider',
              })}
              suffixIcon={<ApiOutlined/>}
              loading={providerVLoading}
              onChange={onVoiceProviderChange}
              options={providerVData?.data?.map((item: ProviderModel) => ({
                key: item.id,
                value: item.id,
                label: item.name,
              }))}
            />
          </Item>
          <Item
            name="voice_model"
            rules={[
              {
                required: true,
                message: formatMessage({
                  id: 'validation.voiceModel',
                }),
              },
            ]}
          >
            <AppSelect
              placeholder={formatMessage({
                id: 'identityStudio.voiceModel',
              })}
              suffixIcon={<RobotOutlined/>}
              loading={voiceLoading}
              disabled={voiceModelData?.data?.length === 0}
              onChange={onVoiceModelChange}
              options={voiceModelData?.data?.map(
                (item: ProviderModel, index: number) => ({
                  key: index,
                  value: item.codename,
                  label: (
                    <StyledModelOption>
                      <Text>{item.name}</Text>
                      <Space>
                        {item.inference && (
                          <Text title="Available on low latency inference">
                            <InfoCircleOutlined/>
                          </Text>
                        )}
                        {item.realtime_sts && (
                          <Text title="This is Realtime(STS) model">
                            <TrademarkOutlined/>
                          </Text>
                        )}
                      </Space>
                    </StyledModelOption>
                  ),
                }),
              )}
            />
          </Item>

          <StyledCollapseItemRow>
            <Item
              name="voice"
              rules={[
                {
                  required: true,
                  message: formatMessage({
                    id: 'validation.synthesizedVoice',
                  }),
                },
              ]}
            >
              {manualVoiceEnabled ? (
                <AppInput
                  placeholder={formatMessage({
                    id: 'identityStudio.synthesizedVoice',
                  })}
                />
              ) : (
                <AppSelect
                  placeholder={formatMessage({
                    id: 'identityStudio.synthesizedVoice',
                  })}
                  suffixIcon={<AudioOutlined/>}
                  disabled={voiceData?.length === 0}
                  options={voiceData?.map((item: ProviderModelVoice) => ({
                    key: item.code,
                    value: item.code,
                    label: item.name,
                  }))}
                />
              )}
            </Item>
          </StyledCollapseItemRow>
          <Item name="manualVoiceId" valuePropName="checked">
            <Checkbox>
              {formatMessage({id: 'voiceConfig.manualVoice'})}
            </Checkbox>
          </Item>

          <Item name="voice_prompt">
            <AppTextArea
              placeholder={formatMessage({
                id: 'voice.voicePrompt',
              })}
              rows={4}
              autoSize={{minRows: 4, maxRows: 6}}
            />
          </Item>
          <Item
            name="voice_temperature"
            style={{flex: 1}}
            label={
              <Text strong>
                {formatMessage({id: 'voice.voiceTemperature'})}
              </Text>
            }
          >
            <TemperatureSlider text={false} min={0.7} max={1.5} step={0.1}/>
          </Item>

          <Item
            name="voice_speed"
            style={{flex: 1}}
            label={
              <Text strong>{formatMessage({id: 'voice.voiceSpeed'})}</Text>
            }
          >
            <TemperatureSlider text={false} min={0.5} max={1.5} step={0.05}/>
          </Item>
        </Fragment>
      ),
      forceRender: true,
    },
  ];

  return (
    <Collapse expandIconPlacement="end" items={items}/>
  );
};

export default VoiceCollapseSection;
