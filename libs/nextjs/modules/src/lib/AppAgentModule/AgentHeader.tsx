import {useEffect, useState} from 'react';
import type {FormInstance, MenuProps} from 'antd';
import {Dropdown, Flex, Form, Space} from 'antd';
import {
  MdDeleteOutline,
  MdMoreVert,
  MdOutlineChat,
  MdOutlineCheckCircle,
  MdOutlineContentCopy,
  MdOutlineMic,
  MdOutlinePhoneEnabled,
  MdOutlineSupportAgent,
} from 'react-icons/md';

import {deleteDataApi, postDataApi, useInfoViewActionsContext,} from '@unpod/providers';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import {StyledContainer, StyledSegmented, StyledTitleContainer, ToggleButton,} from './index.styled';
import AgentTitle from './AgentTitile';
import {useApp} from '@unpod/custom-hooks';
import {useAppModuleActionsContext, useAppModuleContext,} from '@unpod/providers/AppModuleContextProvider';
import {useRouter} from 'next/navigation';
import AppDrawer from '@unpod/components/antd/AppDrawer';
import VoiceAgent from './VoiceAgent';
import {useMediaQuery} from 'react-responsive';
import AppRegionField from '@unpod/components/common/AppRegionField';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';
import {IoDuplicateOutline} from 'react-icons/io5';
import {DesktopWidthQuery} from '@unpod/constants';
import type {Pilot} from '@unpod/constants/types';

import {useIntl} from 'react-intl';
import TestAgent from '@unpod/livekit/AppVoiceAgent/Test/TestAgent';

type AgentHeaderProps = {
  agentData: Pilot;
  saveAgent?: (data: any, state?: string) => void;
  loading?: boolean;
  form: FormInstance;
};

const AgentHeader = ({
                       agentData,
                       saveAgent,
                       loading,
                       form,
                     }: AgentHeaderProps) => {
  const {openConfirmModal} = useApp();
  const infoViewActionsContext = useInfoViewActionsContext();
  const {deleteRecord} = useAppModuleActionsContext();
  const {listData} = useAppModuleContext() as {
    listData: { apiData: Array<{ handle?: string }> };
  };
  const router = useRouter();
  const {addNewRecord} = useAppModuleActionsContext();
  const [isTalkToAgentOpen, setIsTalkToAgentOpen] = useState(false);
  const [isTestAgentOpen, setIsTestAgentOpen] = useState(false);
  const {formatMessage} = useIntl();

  const desktopScreen = useMediaQuery(DesktopWidthQuery);

  useEffect(() => {
    const payload: Record<string, any> = {
      name: agentData?.name,
      type: agentData?.type || 'Voice',
      handle: agentData?.handle,
    };
    if (!agentData?.handle) {
      payload.region = 'IN';
    }
    form.setFieldsValue(payload);
  }, [agentData, form]);

  const onSaveHeaderData = (state?: string) => {
    form.validateFields().then(() => {
      const payload: Record<string, any> = {
        type: form.getFieldValue('type'),
        name: form.getFieldValue('name'),
        handle: form.getFieldValue('handle'),
      };
      if (!agentData?.handle) payload.region = form.getFieldValue('region');
      saveAgent?.({...agentData, ...payload}, state);
    });
  };

  const onSetHeaderData = (state?: string) => {
    onSaveHeaderData(state);
  };

  const onAgentDelete = () => {
    deleteRecord(agentData.handle as string);
    if (listData.apiData.length > 1) {
      if (listData.apiData[0].handle === agentData.handle) {
        router.push(`/ai-studio/${listData.apiData[1].handle}`);
      } else {
        router.push(`/ai-studio/${listData.apiData[0].handle}`);
      }
    } else {
      router.push(`/ai-studio/new/`);
    }
  };

  const onDelete = () => {
    deleteDataApi(`core/pilots/${agentData?.handle}/`, infoViewActionsContext)
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        onAgentDelete();
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };
  const onDuplicateAgent = () => {
    postDataApi<Pilot>(
      `core/pilots/${agentData?.handle}/clone/`,
      infoViewActionsContext,
      {
        handle: agentData?.handle,
      },
    )
      .then((data: any) => {
        infoViewActionsContext.showMessage(data.message);
        addNewRecord(data.data);
        router.push(`/ai-studio/${data.data.handle}`);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onTalkToAgent = () => {
    setIsTalkToAgentOpen(true);
  };

  const onMenuClick: MenuProps['onClick'] = ({key}) => {
    if (key === 'delete') {
      openConfirmModal({
        content: formatMessage({id: 'identityStudio.deleteConfirm'}),
        onOk: onDelete,
      });
    } else if (key === 'chat') {
      form.setFieldsValue({type: 'Message'});
      onSetHeaderData('draft');
    } else if (key === 'voice') {
      form.setFieldsValue({type: 'Voice'});
      onSetHeaderData('draft');
    } else if (key === 'talk') {
      onTalkToAgent();
    } else if (key === 'test-agent') {
      setIsTestAgentOpen(true);
    } else if (key === 'duplicate') {
      onDuplicateAgent();
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
      <ToggleButton
        active={agentData?.type === 'Message'}
        disabled={!agentData?.handle}
        onClick={() => onMenuClick({key: 'chat'} as any)}
        aria-disabled={!agentData?.handle}
      >
        <MdOutlineChat/>
      </ToggleButton>
      <ToggleButton
        active={agentData?.type === 'Voice'}
        disabled={!agentData?.handle}
        onClick={() => onMenuClick({key: 'voice'} as any)}
        aria-disabled={!agentData?.handle}
      >
        <MdOutlineMic/>
      </ToggleButton>
    </div>
  );

  const menus = [
    ...(desktopScreen
      ? [
        {
          key: 'toggle',
          label: <ChatVoiceToggle/>,
          disabled: true,
        },
        {
          type: 'divider' as const,
        },
        {
          key: 'talk',
          label: (
            <span style={{display: 'inline-flex', alignItems: 'center'}}>
                <MdOutlinePhoneEnabled fontSize={18}/>
                <span style={{marginLeft: 8}}>
                  {formatMessage({id: 'common.talkToAgent'})}
                </span>
              </span>
          ),
          disabled: !agentData?.handle,
        },
      ]
      : []),
    {
      key: 'test-agent',
      label: (
        <span style={{display: 'inline-flex', alignItems: 'center'}}>
          <MdOutlineSupportAgent fontSize={18}/>
          <span style={{marginLeft: 8}}>Test Agent</span>
        </span>
      ),
      disabled: !agentData?.handle,
    },
    {
      key: 'duplicate',
      label: (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
          }}
        >
          <IoDuplicateOutline fontSize={16}/>
          <span style={{marginLeft: 8}}>
            {formatMessage({id: 'aiStudio.copyAgent'})}
          </span>
        </span>
      ),
    },
    {
      key: 'copy_handle',
      label: (
        <AppCopyToClipboard
          title={formatMessage({id: 'aiStudio.copyHandle'})}
          text={agentData?.handle}
          hideIcon={false}
        />
      ),
      icon: (
        <span className="ant-icon">
          <MdOutlineContentCopy fontSize={16}/>
        </span>
      ),
    },
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
          <MdDeleteOutline fontSize={18}/>
          <span style={{marginLeft: 8, color: '#ff4d4f'}}>
            {formatMessage({id: 'common.delete'})}
          </span>
        </span>
      ),
    },
  ] as MenuProps['items'];

  return (
    <StyledContainer>
      <Form form={form} initialValues={agentData}>
        <Flex justify="space-between">
          <StyledTitleContainer>
            <AgentTitle
              agentData={agentData}
              onSave={onSaveHeaderData}
              onClose={() => form.setFieldValue('name', agentData?.name)}
            />
            {/*<Tooltip*/}
            {/*  title={*/}
            {/*    <AppCopyToClipboard*/}
            {/*      title="Copy Handle"*/}
            {/*      text={agentData?.handle}*/}
            {/*      hideIcon={false}*/}
            {/*      textColor="white"*/}
            {/*    />*/}
            {/*  }*/}
            {/*>*/}
            {/*  {agentData?.handle && (*/}
            {/*    <StyledAgentInput className="space-agent-token">*/}
            {/*      <Text type="secondary">*/}
            {/*        {agentData?.handle || 'Agent Handle...'}*/}
            {/*      </Text>*/}
            {/*    </StyledAgentInput>*/}
            {/*  )}*/}
            {/*</Tooltip>*/}
          </StyledTitleContainer>

          <Space align="start">
            {!agentData?.handle && <AppRegionField/>}

            {!desktopScreen && (
              <>
                <StyledSegmented
                  shape="round"
                  size="large"
                  value={agentData?.type}
                  onChange={(type) => {
                    form.setFieldsValue({type});
                    onSetHeaderData('draft');
                  }}
                  options={[
                    {
                      label: formatMessage({id: 'aiStudio.ChatButton'}),
                      value: 'Message',
                      icon: <MdOutlineChat fontSize={18}/>,
                      disabled: !agentData?.handle,
                    },
                    {
                      label: formatMessage({id: 'aiStudio.VoiceButton'}),
                      value: 'Voice',
                      icon: <MdOutlineMic fontSize={18}/>,
                      disabled: !agentData?.handle,
                    },
                  ]}
                />

                <AppHeaderButton
                  shape="round"
                  size="small"
                  icon={<MdOutlinePhoneEnabled fontSize={18}/>}
                  disabled={!agentData?.handle}
                  onClick={onTalkToAgent}
                >
                  {formatMessage({id: 'common.talkToAgent'})}
                </AppHeaderButton>
              </>
            )}

            <AppHeaderButton
              type="primary"
              shape="round"
              size="small"
              icon={<MdOutlineCheckCircle fontSize={desktopScreen ? 22 : 18}/>}
              onClick={() => onSetHeaderData('published')}
              loading={loading}
            >
              {desktopScreen ? '' : formatMessage({id: 'agent.publish'})}
            </AppHeaderButton>

            {agentData && (
              <Dropdown
                menu={{items: menus, onClick: onMenuClick}}
                trigger={['click']}
                placement="bottomRight"
              >
                <AppHeaderButton
                  shape="circle"
                  size="small"
                  icon={<MdMoreVert fontSize={16}/>}
                />
              </Dropdown>
            )}
          </Space>
        </Flex>
      </Form>

      <AppDrawer
        open={isTalkToAgentOpen}
        onClose={() => setIsTalkToAgentOpen(false)}
        padding="0"
        title={formatMessage({id: 'common.talkToAgent'})}
        closable
        overflowY="hidden"
      >
        {isTalkToAgentOpen ? <VoiceAgent agentData={agentData}/> : null}
      </AppDrawer>

      <AppDrawer
        open={isTestAgentOpen}
        onClose={() => setIsTestAgentOpen(false)}
        padding="0"
        // title={formatMessage({ id: 'common.talkToAgent' })}
        title={'🎙️ Agent Testing'}
        size={500}
        overflowY="hidden"
      >
        {isTestAgentOpen ? <TestAgent agentData={agentData}/> : null}
      </AppDrawer>
    </StyledContainer>
  );
};

export default AgentHeader;
