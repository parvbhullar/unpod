import { ReactNode } from 'react';
import { Button, Flex, Form, Space } from 'antd';
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
} from '../index.styled';
import { useIntl } from 'react-intl';

const { useForm, Item } = Form;
// const { Title, Text } = Typography;

type ModelFormProps = {
  agentData?: any;
  updateAgentData?: (data: FormData) => void;
  headerForm?: any;
};

const ModelForm = ({ agentData, updateAgentData }: ModelFormProps) => {
  // const [selectedEvalKeys, setSelectedEvalKeys] = useState<React.Key[]>(
  //   () => [
  //     ...(agentData?.realtime_evals && agentData?.eval_agent
  //       ? [`agent-${agentData.handle}`]
  //       : []),
  //     ...(agentData?.eval_kn_bases || []).map((slug: string) => `kb-${slug}`),
  //   ],
  // );

  const [form] = useForm();
  // const [questionsFields, setQuestionsFields] = useState([]);
  const { formatMessage } = useIntl();
  // const realtime_evals = useWatch('realtime_evals', form);
  // const selectedKB = useWatch('knowledgeBase', form);

  const { activeOrg } = useAuthContext();
  const infoViewContext = useInfoViewContext();

  const [{ apiData: kbData }] = useGetDataApi(
    'spaces/?space_type=knowledge_base&case=all',
    { data: [] },
  ) as [{ apiData: { data?: any[] } }, any];

  const onFinish = (values: any) => {
    const formData = new FormData();
    formData.append('greeting_message', values.greeting_message || '');
    formData.append('system_prompt', values.system_prompt || '');
    formData.append(`conversation_tone`, values.conversation_tone);
    // formData.append('realtime_evals', values.realtime_evals);

    // if (values.realtime_evals && selectedEvalKeys.length) {
    //   const selectedAgent = selectedEvalKeys.find((key: any) =>
    //     key.startsWith('agent-'),
    //   );
    //
    //   const selectedKBs = selectedEvalKeys
    //     .filter((key: any) => key.startsWith('kb-'))
    //     .map((key: any) => key.replace('kb-', ''));
    //
    //   if (selectedAgent) {
    //     formData.append('eval_agent', selectedAgent.replace('agent-', ''));
    //   }
    //
    //   selectedKBs.forEach((kbSlug: any) => {
    //     formData.append('eval_kn_bases', kbSlug);
    //   });
    // }

    if (values.template) {
      formData.append(`template`, values.template.name);
    }
    formData.append('name', agentData?.name || '');

    (values.knowledgeBase || []).forEach((kb: string) =>
      formData.append(`knowledge_bases`, kb),
    );
    updateAgentData?.(formData);
  };

  // const handleEvalResponse = ({ response }: { response: any }) => {
  //   if (response?.data) {
  //     console.log('Second API response any:', response.data);
  //   }
  // };

  const kbList = Array.isArray(kbData?.data) ? kbData.data : [];

  const options = kbList.map((kb: any) => ({
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

  // const tableData = [
  //   {
  //     key: `agent-${agentData?.handle}`,
  //     name: agentData?.name || 'Agent',
  //     actions: (
  //       <Flex justify={'center'}>
  //         <GenerateEvalButton
  //           type="pilot"
  //           token={agentData?.handle}
  //           buttonType="default"
  //           size="small"
  //           onClick={handleEvalResponse}
  //         />
  //       </Flex>
  //     ),
  //   },
  //   ...kbList
  //     .filter((kb: any) => (selectedKB || []).includes(kb.slug))
  //     .map((kb: any) => ({
  //       key: `kb-${kb.slug}`,
  //       name: kb.name,
  //       actions: (
  //         <Flex justify="center">
  //           <GenerateEvalButton
  //             type="Knowledgebase"
  //             token={kb.token}
  //             buttonType="default"
  //             size="small"
  //             onClick={handleEvalResponse}
  //           />
  //         </Flex>
  //       ),
  //     })),
  // ];
  //
  // const columns = [
  //   {
  //     title: 'Name',
  //     dataIndex: 'name',
  //     key: 'name',
  //   },
  //   {
  //     title: formatMessage({ id: 'apiKey.actions' }),
  //     dataIndex: 'actions',
  //     key: 'actions',
  //   },
  // ];

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
        // realtime_evals: agentData?.realtime_evals || false,
        // eval_kn_bases: agentData?.eval_kn_bases,
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
            {/*<StyledRowItem className="borderless">*/}
            {/*  <StyledContent>*/}
            {/*    <Title level={5}>Real Time Evals</Title>*/}
            {/*    <Text type="secondary">*/}
            {/*      {formatMessage({ id: 'advanced.enableDesc' })}*/}
            {/*    </Text>*/}
            {/*  </StyledContent>*/}
            {/*  <Item name="realtime_evals" noStyle>*/}
            {/*    <Switch />*/}
            {/*  </Item>*/}
            {/*</StyledRowItem>*/}

            {/*{realtime_evals && (*/}
            {/*  <AppTable*/}
            {/*    columns={columns}*/}
            {/*    dataSource={tableData}*/}
            {/*    rowKey="key"*/}
            {/*    rowSelection={{*/}
            {/*      type: 'checkbox',*/}
            {/*      selectedRowKeys: selectedEvalKeys as React.Key[],*/}
            {/*      onChange: (selectedRowKeys: React.Key[]) => {*/}
            {/*        setSelectedEvalKeys(selectedRowKeys);*/}
            {/*      },*/}
            {/*    }}*/}
            {/*    pagination={false}*/}
            {/*    size="middle"*/}
            {/*    fullHeight={true}*/}
            {/*  />*/}
            {/*)}*/}
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
