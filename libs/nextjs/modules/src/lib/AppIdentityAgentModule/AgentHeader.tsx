import { useEffect, useState } from 'react';
import type { FormInstance, MenuProps } from 'antd';
import { Dropdown, Flex, Form, Space } from 'antd';
import { useIntl } from 'react-intl';
import {
  MdDelete,
  MdMoreVert,
  MdOutlineChat,
  MdOutlineCheckCircle,
  MdOutlineContentCopy,
  MdOutlineMic,
  MdOutlinePhoneEnabled,
} from 'react-icons/md';
import { deleteDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import { StyledContainer, StyledTitleContainer } from './index.styled';
import AgentTitle from '../AppAgentModule/AgentTitile';
import { useApp } from '@unpod/custom-hooks';
import {
  useAppModuleActionsContext,
  useAppModuleContext,
} from '@unpod/providers/AppModuleContextProvider';
import { useRouter } from 'next/navigation';
import VoiceAgent from '../AppAgentModule/VoiceAgent';
import { useMediaQuery } from 'react-responsive';
import AppRegionField from '@unpod/components/common/AppRegionField';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';
import { DesktopWidthQuery } from '@unpod/constants';
import AppDrawer from '@unpod/components/antd/AppDrawer';

type AgentData = {
  name?: string;
  type?: string;
  handle?: string;
  region?: string;
};

type AgentHeaderProps = {
  agentData?: AgentData;
  saveAgent: (payload: AgentData, state: string) => void;
  loading?: boolean;
  form: FormInstance;
};

const AgentHeader = ({
  agentData,
  saveAgent,
  loading,
  form,
}: AgentHeaderProps) => {
  const { formatMessage } = useIntl();
  const { openConfirmModal } = useApp();
  const infoViewActionsContext = useInfoViewActionsContext();
  const { deleteRecord } = useAppModuleActionsContext();
  const { listData } = useAppModuleContext() as any;
  const router = useRouter();
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);

  const mobileScreen = useMediaQuery(DesktopWidthQuery);

  useEffect(() => {
    const payload: AgentData = {
      name: agentData?.name,
      type: agentData?.type || 'Message',
      handle: agentData?.handle,
    };
    if (!agentData?.handle) {
      payload.region = 'IN';
    }
    form.setFieldsValue(payload);
  }, [agentData, form]);

  const onSaveHeaderData = (state: string) => {
    form.validateFields().then(() => {
      const payload: AgentData = {
        type: form.getFieldValue('type'),
        name: form.getFieldValue('name'),
        handle: form.getFieldValue('handle'),
      };
      if (!agentData?.handle) payload.region = form.getFieldValue('region');
      saveAgent({ ...(agentData || {}), ...payload }, state);
    });
  };

  const onSetHeaderData = (state: string) => {
    onSaveHeaderData(state);
  };

  const onAgentDelete = () => {
    deleteRecord(agentData?.handle as string);
    if (listData?.apiData?.length > 1) {
      if (listData.apiData[0].handle === agentData?.handle) {
        router.push(`/ai-identity-studio/${listData.apiData[1].handle}`);
      } else {
        router.push(`/ai-identity-studio/${listData.apiData[0].handle}`);
      }
    } else {
      router.push(`/ai-identity-studio/new/`);
    }
  };

  const onDelete = () => {
    deleteDataApi(
      `core/pilots/${agentData?.handle}/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        onAgentDelete();
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onTalkToAgent = () => {
    setIsWidgetOpen(true);
  };

  const onMenuClick = ({ key }: { key: string }) => {
    if (key === 'delete') {
      openConfirmModal({
        content: formatMessage({ id: 'identityStudio.deleteConfirm' }),
        onOk: onDelete,
      });
    }
    if (key === 'chat') {
      form.setFieldsValue({ type: 'Message' });
      onSetHeaderData('draft');
    }
    if (key === 'voice') {
      form.setFieldsValue({ type: 'Voice' });
      onSetHeaderData('draft');
    }
    if (key === 'talk') {
      onTalkToAgent();
    }
    if (key === 'publish') {
      onSetHeaderData('published');
    }
  };

  const ChatVoiceToggle = () => (
    <div
      style={{
        display: 'flex',
        background: '#f5f5f5',
        padding: '2px 4px',
        marginBottom: 8,
        width: '100%',
        justifyContent: 'center',
        gap: 4,
      }}
    >
      <span
        onClick={() => onMenuClick({ key: 'chat' })}
        style={{
          background: agentData?.type === 'Message' ? '#6c47ff' : 'transparent',
          color: agentData?.type === 'Message' ? '#fff' : '#888',
          padding: '4px 16px',
          display: 'inline-flex',
          alignItems: 'center',
          fontWeight: 500,
          fontSize: 16,
          cursor: agentData?.handle ? 'pointer' : 'not-allowed',
          opacity: agentData?.handle ? 1 : 0.5,
          transition: 'background 0.2s',
        }}
        aria-disabled={!agentData?.handle}
      >
        <MdOutlineChat style={{ marginRight: 8 }} />
      </span>
      <span
        onClick={() => onMenuClick({ key: 'voice' })}
        style={{
          background: agentData?.type === 'Voice' ? '#6c47ff' : 'transparent',
          color: agentData?.type === 'Voice' ? '#fff' : '#888',
          padding: '4px 16px',
          display: 'inline-flex',
          alignItems: 'center',
          fontWeight: 500,
          fontSize: 16,
          cursor: agentData?.handle ? 'pointer' : 'not-allowed',
          opacity: agentData?.handle ? 1 : 0.5,
          transition: 'background 0.2s',
        }}
        aria-disabled={!agentData?.handle}
      >
        <MdOutlineMic style={{ marginRight: 8 }} />
      </span>
    </div>
  );

  const menus: MenuProps['items'] = [
    ...(mobileScreen
      ? [
          {
            key: 'toggle',
            label: <ChatVoiceToggle />,
            disabled: true,
          },
          {
            type: 'divider' as const,
          },
          {
            key: 'talk',
            label: (
              <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                <MdOutlinePhoneEnabled fontSize={18} />
                <span style={{ marginLeft: 8 }}>
                  {formatMessage({ id: 'common.talkToAgent' })}
                </span>
              </span>
            ),
            disabled: !agentData?.handle,
          },
          {
            key: 'publish',
            label: (
              <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                <MdOutlineCheckCircle fontSize={18} />
                <span style={{ marginLeft: 8 }}>
                  {formatMessage({ id: 'agent.publish' })}
                </span>
              </span>
            ),
          },
        ]
      : []),
    {
      key: 'delete',
      label: (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            color: '#ff4d4f',
          }}
        >
          <MdDelete fontSize={16} />
          <span style={{ marginLeft: 8, color: '#ff4d4f' }}>
            {formatMessage({ id: 'common.delete' })}
          </span>
        </span>
      ),
    },
    {
      key: 'copy_handle',
      label: (
        <AppCopyToClipboard
          title={formatMessage({ id: 'identityStudio.copyHandle' })}
          text={agentData?.handle}
          hideIcon={false}
        />
      ),
      icon: (
        <span className="ant-icon">
          <MdOutlineContentCopy fontSize={16} />
        </span>
      ),
    },
  ];

  return (
    <StyledContainer>
      <Form form={form} initialValues={agentData}>
        <Flex justify="space-between">
          <StyledTitleContainer>
            <AgentTitle
              agentData={agentData}
              onSave={() => onSaveHeaderData('draft')}
              onClose={() => form.setFieldValue('name', agentData?.name)}
            />
          </StyledTitleContainer>

          <Space align="start">
            {!agentData?.handle && <AppRegionField />}

            {!mobileScreen && (
              <>
                <AppHeaderButton
                  shape="round"
                  size="small"
                  icon={<MdOutlinePhoneEnabled fontSize={18} />}
                  disabled={!agentData?.handle}
                  onClick={onTalkToAgent}
                >
                  {formatMessage({ id: 'common.talkToAgent' })}
                </AppHeaderButton>

                <AppHeaderButton
                  type="primary"
                  shape="round"
                  size="small"
                  icon={<MdOutlineCheckCircle fontSize={18} />}
                  onClick={() => onSetHeaderData('published')}
                  loading={loading}
                >
                  {formatMessage({ id: 'agent.publish' })}
                </AppHeaderButton>
              </>
            )}

            {agentData && (
              <Dropdown
                menu={{ items: menus, onClick: onMenuClick }}
                trigger={['click']}
                placement="bottomRight"
              >
                <AppHeaderButton
                  shape="circle"
                  size="small"
                  icon={<MdMoreVert fontSize={16} />}
                />
              </Dropdown>
            )}
          </Space>
        </Flex>
      </Form>

      <AppDrawer
        open={isWidgetOpen}
        onClose={() => setIsWidgetOpen(false)}
        width={400}
        title={formatMessage({ id: 'common.talkToAgent' })}
        maskClosable={false}
        closable
        keyboard={false}
      >
        {isWidgetOpen ? <VoiceAgent agentData={agentData} /> : null}
      </AppDrawer>
    </StyledContainer>
  );
};

export default AgentHeader;
