import React, { ReactNode, useState } from 'react';
import { Button, Flex, Form, Space, Switch, Typography } from 'antd';
import {
  DatabaseOutlined,
  MessageOutlined,
  SaveOutlined,
} from '@ant-design/icons';
import { AppInput, AppSelect } from '@unpod/components/antd';
import {
  useAuthContext,
  useGetDataApi,
  useInfoViewContext,
} from '@unpod/providers';
import { getPostIcon } from '@unpod/helpers/PermissionHelper';
import {
  StyledSelectDesc,
  StyledSelectLabel,
  StyledSelectWrapper,
} from './index.styled';
import CardWrapper from '@unpod/components/common/CardWrapper';
import PersonaForm from '../../AppIdentityAgentModule/Persona/PersonaForm';
import {
  StickyFooter,
  StyledMainContainer,
  StyledTabRoot,
  StyledContent
} from '../index.styled';
import { useIntl } from 'react-intl';
import AppTable from '@unpod/components/third-party/AppTable';
import { StyledRowItem } from '../AdvancedForm/index.styled';
import { KnowledgeBase, Pilot } from '@unpod/constants/types';
import type { FormInstance } from 'antd/es/form';
import { getEvalColumns } from './getEvalColumns';

const { useForm, Item, useWatch } = Form;
const { Title, Text } = Typography;

type ModelFormProps = {
  agentData: Pilot;
  updateAgentData?: (data: FormData) => void;
  headerForm?: FormInstance;
};

export type EvalRow = {
  key: string;
  type: 'agent' | 'kb';
  name: string;
  evalName?: string;
  evalSlug?: string;
  token: string;
  hasEval: boolean;
  status?: string | undefined;
};

export type AgentConfigFormValues = {
  greeting_message?: string;
  system_prompt?: string;
  conversation_tone: string;
  realtime_evals?: boolean;
  knowledgeBase?: string[];
};

const ModelForm = ({ agentData, updateAgentData }: ModelFormProps) => {
  const [selectedEvalKeys, setSelectedEvalKeys] = useState<React.Key[]>(() => [
    ...((agentData?.eval_kn_bases || []) as string[]),
  ]);
  const [evalsData, setEvalsData] = useState<Record<string, KnowledgeBase>>({});

  const [form] = useForm();
  // const [questionsFields, setQuestionsFields] = useState([]);
  const { formatMessage } = useIntl();
  const realtime_evals = useWatch('realtime_evals', form);
  const selectedKB = useWatch('knowledgeBase', form);

  const { activeOrg } = useAuthContext();
  const infoViewContext = useInfoViewContext();

  const [{ apiData: kbData }, { reCallAPI }] = useGetDataApi<KnowledgeBase[]>(
    'spaces/?space_type=knowledge_base&case=pilot',
    { data: [] },
  );

  const onFinish = (values: AgentConfigFormValues) => {
    const formData = new FormData();
    formData.append('greeting_message', values.greeting_message || '');
    formData.append('system_prompt', values.system_prompt || '');
    formData.append(`conversation_tone`, values.conversation_tone);
    formData.append('realtime_evals', String(values.realtime_evals ?? false));

    if (values.realtime_evals) {
      const tableMap = new Map(tableData.map((row) => [row.key, row]));

      selectedEvalKeys.forEach((key) => {
        const row = tableMap.get(String(key));
        if (!row || !row.evalSlug) return;

        // if (row.type === 'agent') {
        //   formData.append('eval_agent', row.evalSlug);
        // }

        if (row.type === 'kb') {
          formData.append('eval_kn_bases', row.evalSlug);
        }
      });
    }

    (values.knowledgeBase || []).forEach((kb: string) =>
      formData.append(`knowledge_bases`, kb),
    );
    updateAgentData?.(formData);
  };

  const handleEvalResponse = (
    { response }: { response: KnowledgeBase },
    rowKey: string,
  ) => {
    if (response) {
      setEvalsData((prev) => ({
        ...prev,
        [rowKey]: response,
      }));
      reCallAPI();
    }
  };

  const kbList = Array.isArray(kbData?.data) ? kbData.data : [];

  const options = kbList.map((kb: KnowledgeBase) => ({
    value: kb.slug,
    label: (
      <Space align="start">
        {getPostIcon(kb.privacy_type)}
        <Flex vertical>
          <StyledSelectLabel strong>{kb.name}</StyledSelectLabel>
          {kb.description && (
            <StyledSelectDesc>{kb.description}</StyledSelectDesc>
          )}
        </Flex>
      </Space>
    ),
    labelText: kb.name,
  }));

  const tableData: EvalRow[] = [
    {
      key: agentData?.handle as string,
      type: 'agent',
      name: `${agentData?.name} (Agent)`,
      evalName: evalsData[agentData?.handle as string]?.name as string,
      evalSlug: evalsData[agentData?.handle as string]?.slug,
      token: agentData?.handle as string,
      hasEval: (agentData?.has_evals as boolean) || false,
      status: 'pending',
    },
    ...(kbList
      .filter((kb) => (selectedKB || []).includes(kb.slug))
      .map((kb: KnowledgeBase) => ({
        key: kb.slug,
        type: 'kb',
        name: kb.name,
        evalName: evalsData[kb.slug as string]?.name
          ? evalsData[kb.slug as string]?.name
          : kb?.evals_info?.eval_name,
        evalSlug: evalsData[kb.slug as string]?.slug,
        token: kb.token,
        hasEval: kb.has_evals,
        status: kb.has_evals && kb?.evals_info?.gen_status,
      })) as EvalRow[]),
  ];

  // useEffect(() => {
  //   if (!agentData) return;
  //
  //   const kbKeys = kbList
  //     .filter((kb) =>
  //       (agentData?.eval_kn_bases || []).includes(kb.evals_info?.eval_slug),
  //     )
  //     .map((kb) => kb.slug);
  //
  //   const initialSelectedKeys = [...kbKeys];
  //
  //   setSelectedEvalKeys(initialSelectedKeys);
  // }, [agentData]);

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        greeting_message:
          agentData?.greeting_message || 'Hello! How can I assist you today?',
        system_prompt: agentData?.system_prompt,
        knowledgeBase: agentData?.knowledge_bases,
        conversation_tone: agentData?.conversation_tone,
        realtime_evals: agentData?.realtime_evals || false,
        eval_kn_bases: agentData?.eval_kn_bases,
      }}
      onFinish={onFinish}
    >
      <StyledTabRoot>
        <StyledMainContainer>
          <CardWrapper
            icon={<MessageOutlined />}
            title={formatMessage({ id: 'onboarding.persona' })}
          >
            <Item
              name="greeting_message"
              rules={[
                {
                  required: true,
                  message: formatMessage({ id: 'validation.greetingMassage' }),
                },
              ]}
              help={formatMessage({ id: 'aiStudio.greetingHelp' })}
            >
              <AppInput
                placeholder={formatMessage({
                  id: 'aiStudio.greetingPlaceholder',
                })}
              />
            </Item>

            <PersonaForm form={form} agentData={agentData} />
          </CardWrapper>

          {/* <CardWrapper icon={<BulbOutlined />} title="Objectives">
        <Paragraph type="secondary">
          Define questions or topics for your AI
        </Paragraph>
        <Form.Item name="questions">
          <AIQuestionsFields
            questionsFields={questionsFields}
            setQuestionsFields={setQuestionsFields}
          />
        </Form.Item>
      </CardWrapper>*/}

          <CardWrapper
            icon={<DatabaseOutlined />}
            title={formatMessage({ id: 'aiStudio.knowledgeBase' })}
          >
            <Item
              name="knowledgeBase"
              help={formatMessage({ id: 'aiStudio.knowledgeBaseHelp' })}
            >
              <AppSelect
                mode="multiple"
                allowClear
                virtual={false}
                optionLabelProp="labelText"
                placeholder={formatMessage({
                  id: 'aiStudio.knowledgeBaseSelect',
                })}
                suffixIcon={<DatabaseOutlined />}
                popupRender={(menu: ReactNode) => (
                  <StyledSelectWrapper>{menu}</StyledSelectWrapper>
                )}
                options={options}
              />
            </Item>
            <StyledRowItem className="borderless">
              <StyledContent>
                <Title level={5}>Real Time Evals</Title>
                <Text type="secondary">
                  {formatMessage({ id: 'advanced.enableDesc' })}
                </Text>
              </StyledContent>
              <Item name="realtime_evals" noStyle>
                <Switch />
              </Item>
            </StyledRowItem>

            {realtime_evals && (
              <AppTable<EvalRow>
                columns={getEvalColumns(handleEvalResponse, formatMessage)}
                dataSource={tableData}
                rowKey="key"
                rowSelection={{
                  type: 'checkbox',
                  selectedRowKeys: selectedEvalKeys,
                  onChange: (selectedRowKeys: React.Key[]) => {
                    setSelectedEvalKeys(selectedRowKeys);
                  },
                }}
                pagination={false}
                size="middle"
                fullHeight={true}
              />
            )}
          </CardWrapper>
        </StyledMainContainer>
      </StyledTabRoot>

      <StickyFooter>
        <Flex justify="end">
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={infoViewContext?.loading}
            disabled={!activeOrg?.domain_handle}
          >
            {formatMessage({ id: 'common.save' })}
          </Button>
        </Flex>
      </StickyFooter>
    </Form>
  );
};

export default ModelForm;
