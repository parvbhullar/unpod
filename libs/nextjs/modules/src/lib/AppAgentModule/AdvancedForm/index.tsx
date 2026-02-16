import type { FormInstance } from 'antd';
import { Button, Flex, Form, Switch, Typography } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import {
  useInfoViewActionsContext,
  useInfoViewContext,
} from '@unpod/providers';
import CardWrapper from '@unpod/components/common/CardWrapper';
import dayjs from 'dayjs';
import {
  MdMemory,
  MdOutlinePhoneEnabled,
  MdOutlineVoiceOverOff,
  MdPhoneCallback,
} from 'react-icons/md';
import { clsx } from 'clsx';
import AppTextArea from '@unpod/components/antd/AppTextArea';
import StopSpeakingPlan from './Speacking';
import CallingHours from './CallingHours';
import { StyledContent, StyledRowItem } from './index.styled';
import {
  StickyFooter,
  StyledMainContainer,
  StyledTabRoot,
} from '../index.styled';
import { useIntl } from 'react-intl';
import { AppInput } from '@unpod/components/antd';
import AppPhoneTagSelect from '@unpod/components/antd/AppPhoneTagSelect';
import type { CallingTimeRange, Pilot } from '@unpod/constants/types';

const { Item, useForm } = Form;
const { Title, Text } = Typography;

type AdvancedFormProps = {
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
  headerForm?: FormInstance;
};

type HandoverNumber = {
  region?: string;
  numbers?: string[];
};

export type AgentFormValues = {
  enable_memory?: boolean;
  enable_callback?: boolean;
  notify_via_sms?: boolean;
  enable_followup?: boolean;
  followup_prompt?: string;
  enable_handover?: boolean;
  handover_number: HandoverNumber;
  handover_prompt?: string;
  handover_person_name?: string;
  handover_person_role?: string;
  instant_handover: boolean;
  calling_days?: string[];
  calling_time_ranges?: CallingTimeRange[];
  number_of_words?: number;
  voice_seconds?: number;
  back_off_seconds?: number;
};

const AdvancedForm = ({ agentData, updateAgentData }: AdvancedFormProps) => {
  const infoViewContext = useInfoViewContext();
  const infoViewActionContext = useInfoViewActionsContext();
  const [form] = useForm();
  const { formatMessage } = useIntl();
  const enable_followup = Form.useWatch('enable_followup', form);
  const enable_handover = Form.useWatch('enable_handover', form);

  const onFinish = (values: AgentFormValues) => {
    const formData = new FormData();
    formData.append('type', agentData?.type || '');
    formData.append('enable_memory', String(values.enable_memory));
    formData.append('enable_callback', String(values.enable_callback));
    formData.append('notify_via_sms', String(values.notify_via_sms));
    formData.append('enable_followup', String(values.enable_followup));

    if (enable_followup && values.followup_prompt) {
      formData.append('followup_prompt', values.followup_prompt);
    }

    formData.append('enable_handover', String(values.enable_handover));
    if (enable_handover) {
      const numbersArray = values.handover_number.numbers || [];
      formData.append(
        'handover_number_cc',
        values.handover_number.region || '',
      );
      formData.append('handover_number', numbersArray.join(', '));
      formData.append('handover_prompt', values.handover_prompt || '');
      formData.append(
        'handover_person_name',
        values.handover_person_name || '',
      );
      formData.append(
        'handover_person_role',
        values.handover_person_role || '',
      );
      formData.append('instant_handover', String(values.instant_handover));
    }

    if (values.calling_days && values.calling_time_ranges) {
      const formattedRanges = values.calling_time_ranges.map(
        (item: CallingTimeRange) => ({
          start: item.start?.format('HH:mm'),
          end: item.end?.format('HH:mm'),
        }),
      );

      formData.append('calling_days', JSON.stringify(values.calling_days));
      formData.append('calling_time_ranges', JSON.stringify(formattedRanges));
    } else {
      formData.append('calling_days', JSON.stringify([]));
      formData.append('calling_time_ranges', JSON.stringify([]));
    }
    formData.append('telephony_enabled', String(agentData?.type === 'Voice'));
    formData.append('name', agentData?.name || '');
    formData.append('number_of_words', String(values.number_of_words ?? 0));
    formData.append('voice_seconds', String(values.voice_seconds ?? 0));
    formData.append('back_off_seconds', String(values.back_off_seconds ?? 0));

    // const callbackHeadersMap = values.callback_headers
    //   ? values.callback_headers.reduce(
    //       (acc: Record<string, string>, item: any) => {
    //         if (item.key && item.value) {
    //           acc[item.key] = item.value;
    //         }
    //         return acc;
    //       },
    //       {},
    //     )
    //   : {};
    // formData.append('callback_headers', JSON.stringify(callbackHeadersMap));
    // if (values.callback_url) {
    //   formData.append('callback_url', values.callback_url);
    // }

    updateAgentData?.(formData);
  };

  const onFinishFailed = () => {
    infoViewActionContext.showError(
      formatMessage({ id: 'advanced.saveError' }),
    );
  };

  // const transformHeadersMapToArray = (headersMap?: Record<string, string>) => {
  //   if (!headersMap) {
  //     return [];
  //   }
  //   return Object.entries(headersMap).map(([key, value]) => ({
  //     key: key,
  //     value: value,
  //   }));
  // };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      onFinishFailed={onFinishFailed}
      initialValues={{
        enable_memory: agentData?.enable_memory || false,
        enable_callback: agentData?.enable_callback || false,
        notify_via_sms: agentData?.notify_via_sms || false,
        enable_followup: agentData?.enable_followup || false,
        instant_handover: agentData?.instant_handover || false,
        followup_prompt: agentData?.followup_prompt || false,
        // callback_headers: transformHeadersMapToArray(
        //   agentData?.callback_headers,
        // ),
        enable_handover: agentData?.enable_handover || false,
        handover_number: {
          region: agentData?.handover_number_cc || '+91',
          numbers: agentData?.handover_number
            ? agentData.handover_number
                .split(',')
                .map((num: string) => num.trim())
            : [],
        },
        handover_prompt: agentData?.handover_prompt || '',
        handover_person_name: agentData?.handover_person_name || '',
        handover_person_role: agentData?.handover_person_role || '',
        // callback_url: agentData?.callback_url,
        number_of_words: agentData?.number_of_words || 0,
        voice_seconds: agentData?.voice_seconds || 0,
        back_off_seconds: agentData?.back_off_seconds || 0,
        calling_days:
          agentData?.calling_days && agentData.calling_days.length > 0
            ? agentData.calling_days
            : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        calling_time_ranges:
          (agentData?.calling_time_ranges?.length ?? 0) > 0
            ? agentData.calling_time_ranges?.map((item: CallingTimeRange) => ({
                start: dayjs(item.start, 'HH:mm'),
                end: dayjs(item.end, 'HH:mm'),
              }))
            : [
                {
                  start: dayjs('08:00 AM', 'hh:mm A'),
                  end: dayjs('08:00 PM', 'hh:mm A'),
                },
              ],
      }}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper
            icon={<MdMemory size={16} />}
            title={formatMessage({ id: 'advanced.contextSettings' })}
          >
            <StyledRowItem className="borderless">
              <StyledContent>
                <Title level={5}>
                  {formatMessage({ id: 'advanced.enableMemory' })}
                </Title>
                <Text type="secondary">
                  {formatMessage({ id: 'advanced.enableDesc' })}
                </Text>
              </StyledContent>
              <Item name="enable_memory" noStyle>
                <Switch />
              </Item>
            </StyledRowItem>
          </CardWrapper>

          <CardWrapper
            icon={<MdPhoneCallback />}
            title={formatMessage({ id: 'advanced.autoReachout' })}
          >
            <StyledRowItem className={clsx({ borderless: enable_followup })}>
              <StyledContent>
                <Title level={5}>
                  {formatMessage({ id: 'advanced.enableFollowup' })}
                </Title>
                <Text type="secondary">
                  {formatMessage({ id: 'advanced.enableFollowupDesc' })}
                </Text>
              </StyledContent>
              <Item name="enable_followup" noStyle>
                <Switch />
              </Item>
            </StyledRowItem>

            {enable_followup && (
              <StyledRowItem>
                <StyledContent>
                  <Form.Item name="followup_prompt" noStyle>
                    <AppTextArea
                      placeholder={formatMessage({
                        id: 'advanced.followupInstructions',
                      })}
                      rows={4}
                      autoSize={{ minRows: 4, maxRows: 6 }}
                    />
                  </Form.Item>
                </StyledContent>
              </StyledRowItem>
            )}

            <StyledRowItem>
              <StyledContent>
                <Title level={5}>
                  {formatMessage({ id: 'advanced.instantRedial' })}
                </Title>
                <Text type="secondary">
                  {formatMessage({ id: 'advanced.instantRedialDesc' })}
                </Text>
              </StyledContent>
              <Item name="enable_callback" noStyle>
                <Switch />
              </Item>
            </StyledRowItem>

            <StyledRowItem>
              <StyledContent>
                <Title level={5}>
                  {formatMessage({ id: 'advanced.notifyViaSMS' })}
                </Title>
                <Text type="secondary">
                  {formatMessage({ id: 'advanced.notifyViaSMSDesc' })}
                </Text>
              </StyledContent>
              <Item name="notify_via_sms" noStyle>
                <Switch />
              </Item>
            </StyledRowItem>

            <StyledRowItem className="borderless">
              <StyledContent>
                <Title level={5}>
                  {formatMessage({ id: 'advanced.handoverNumber' })}
                </Title>
                <Text type="secondary">
                  {formatMessage({ id: 'advanced.handoverNumberDesc' })}
                </Text>
              </StyledContent>

              <Item name="enable_handover" noStyle>
                <Switch />
              </Item>
            </StyledRowItem>

            {enable_handover && (
              <>
                <StyledRowItem className="borderless">
                  <StyledContent>
                    <Title level={5}>
                      {formatMessage({ id: 'advanced.instantHandover' })}
                    </Title>
                    <Text type="secondary">
                      {formatMessage({ id: 'advanced.instantHandoverDesc' })}
                    </Text>
                  </StyledContent>

                  <Item name="instant_handover" noStyle>
                    <Switch />
                  </Item>
                </StyledRowItem>

                <Item
                  style={{ marginTop: 12 }}
                  name="handover_number"
                  rules={[
                    {
                      required: enable_handover,
                      message: formatMessage({
                        id: 'validation.handoverNumber',
                      }),
                    },
                  ]}
                >
                  <AppPhoneTagSelect
                    placeholder={formatMessage({ id: 'form.phoneNumber' })}
                    suffixIcon={<MdOutlinePhoneEnabled fontSize={16} />}
                  />
                </Item>

                <Item name="handover_prompt" noStyle>
                  <AppTextArea
                    placeholder={formatMessage({
                      id: 'advanced.handoverInstructions',
                    })}
                    rows={4}
                    autoSize={{ minRows: 4, maxRows: 6 }}
                  />
                </Item>

                <Item name="handover_person_role" noStyle>
                  <AppInput placeholder={formatMessage({ id: 'form.role' })} />
                </Item>
              </>
            )}
          </CardWrapper>

          <CardWrapper
            title={formatMessage({ id: 'advanced.callingHours' })}
            icon={<MdPhoneCallback size={16} />}
          >
            <StyledRowItem className="borderless">
              <StyledContent>
                <CallingHours />
              </StyledContent>
            </StyledRowItem>
          </CardWrapper>

          <CardWrapper
            title={formatMessage({ id: 'advanced.stopSpeakingPlan' })}
            icon={<MdOutlineVoiceOverOff />}
          >
            <StyledRowItem className="borderless">
              <StyledContent>
                <StopSpeakingPlan />
              </StyledContent>
            </StyledRowItem>
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
            {formatMessage({ id: 'common.save' })}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default AdvancedForm;
