import {useMemo, useState} from 'react';
import type {MenuProps} from 'antd';
import {App, Dropdown, Modal, Space, Tooltip} from 'antd';
import {MdAdd, MdCall, MdMoreVert, MdOutlineContentCopy, MdOutlineDownload,} from 'react-icons/md';
import {useRouter} from 'next/navigation';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import {isEditAccessAllowed} from '@unpod/helpers/PermissionHelper';
import {
  deleteDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import {AppDrawer} from '@unpod/components/antd';
import EditSpace from './EditSpace';
import DownloadLogs from './DownloadLogs';
import {StyledHeader} from './index.styled';
import {AiOutlineEdit} from 'react-icons/ai';
import ConfigureAgentModal from './ConfigureAgent';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';
import {useIntl} from 'react-intl';
import AppSpaceCallModal from '@unpod/components/modules/AppSpaceContactCall/AppSpaceCallModal';
import DocSelector from '../../MainContent/Content/Calls/DocSelector';

const SidebarHeader = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();
  const {
    setActiveTab,
    setActiveConversation,
    setActiveNote,
    setActiveDocument,
    setSelectedDocs,
  } = useAppSpaceActionsContext();
  const {currentSpace, activeTab, connectorData} = useAppSpaceContext();
  const {formatMessage} = useIntl();
  const {modal} = App.useApp();

  const [addNew, setAddNew] = useState(false);
  const [isEditOpen, setEditOpen] = useState(false);
  const [downloadLog, setDownloadLog] = useState(false);
  const [isConfigureOpen, setIsConfigureOpen] = useState<boolean>(false);
  const [isCallModalOpen, setCallModalOpen] = useState(false);
  const [visible, setVisible] = useState(false);
  const showCallIcon = activeTab === 'call' || activeTab === 'doc';
  const isMobile =
    typeof window !== 'undefined' ? window.innerWidth <= 576 : false;

  const items = useMemo<MenuProps['items']>(() => {
    const options = [
      {
        key: 'actions',
        label: formatMessage({id: 'space.edit'}),
        icon: (
          <span className="ant-icon">
            <AiOutlineEdit fontSize={18}/>
          </span>
        ),
      },
      {
        key: 'copy_slug',
        label: (
          <AppCopyToClipboard
            title={formatMessage({id: 'space.spaceToken'})}
            text={currentSpace?.token}
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
        key: 'download',
        label: formatMessage({id: 'space.callLogs'}),
        icon: (
          <span className="ant-icon">
            <MdOutlineDownload fontSize={20}/>
          </span>
        ),
      },
      /*{
        key: 'dashboard',
        label: 'Analytics',
        icon: (
          <span className="ant-icon">
            <MdOutlineSpaceDashboard fontSize={16} />
          </span>
        ),
      },
      {
        key: 'configure-agent',
        label: 'Link Agent',
        icon: (
          <span className="ant-icon">
            <AiOutlineApi fontSize={16} />
          </span>
        ),
      },*/
    ];

    return options;
  }, [currentSpace]);

  const onArchiveSpace = () => {
    deleteDataApi(`spaces/${currentSpace?.slug}/`, infoViewActionsContext)
      .then((response) => {
        const res = response as { message?: string };
        if (res.message) infoViewActionsContext.showMessage(res.message);
        router.push(`/spaces/`);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const confirmArchiveSpace = () => {
    Modal.confirm({
      title: 'Confirm Archive Space',
      icon: null,
      content: 'Are you sure you want to archive this space?',
      okText: 'Archive',
      cancelText: 'Cancel',
      onOk: onArchiveSpace,
    });
  };

  // Get dynamic tooltip title based on active tab
  const getAddButtonTooltip = useMemo(() => {
    switch (activeTab) {
      case 'chat':
        return formatMessage({id: 'space.startNewThread'});
      case 'note':
      case 'notes':
        return formatMessage({id: 'space.addNewNote'});
      case 'doc':
        return formatMessage({id: 'peopleSidebarMenu.callAll'});
      case 'logs':
      case 'call':
        return formatMessage({id: 'space.addNewCall'});
      case 'dashboard':
      case 'analytics':
        return formatMessage({id: 'space.addWidget'});
      default:
        return formatMessage({id: 'space.addChannel'});
    }
  }, [activeTab, formatMessage]);

  // Handle add button click based on active tab
  const handleAddButtonClick = () => {
    const spaceSlug = currentSpace?.slug;
    switch (activeTab) {
      case 'chat':
        // Start new thread/conversation
        setActiveConversation(null);
        setActiveTab('chat');
        if (spaceSlug) router.push(`/spaces/${spaceSlug}/chat`);
        break;
      case 'note':
      case 'notes':
        // Add new note
        setActiveNote(null);
        setActiveTab('note');
        if (spaceSlug) router.push(`/spaces/${spaceSlug}/note`);
        break;
      case 'doc':
        modal.confirm({
          title: formatMessage({id: 'peopleHeader.title'}),
          content: formatMessage({id: 'peopleHeader.content'}),
          okText: formatMessage({id: 'peopleHeader.okButton'}),
          cancelText: formatMessage({id: 'common.cancel'}),
          okButtonProps: {danger: true},
          centered: true,
          onOk: () => {
            setCallModalOpen(true);
            setSelectedDocs(
              connectorData?.apiData.map((doc: any) => doc.document_id),
            );
          },
        });
        // setActiveDocument(null);
        // setDocumentMode('add');
        // router.push(`/spaces/${currentSpace.slug}/doc`);
        break;
      case 'logs':
      case 'call':
        // Open call modal to schedule/make a new call
        setVisible(true);
        break;
      case 'dashboard':
      case 'analytics':
        // Add widget or navigate to dashboard root
        setActiveTab('dashboard');
        if (spaceSlug) router.push(`/spaces/${spaceSlug}?t=dashboard`);
        break;
      default:
        // Default: open channels drawer
        break;
    }
  };

  const onMenuClick: MenuProps['onClick'] = (item) => {
    const spaceSlug = currentSpace?.slug;
    if (item.key === 'actions') {
      setEditOpen(true);
    } else if (item.key === 'archive-space') {
      confirmArchiveSpace();
    } else if (item.key === 'configure-agent') {
      setIsConfigureOpen(true);
      // router.push(`/configure-agent/${currentSpace?.slug}`);
    } else if (item.key === 'dashboard') {
      setActiveTab('dashboard');
      if (spaceSlug) router.replace(`/spaces/${spaceSlug}?t=dashboard`);
      setActiveConversation(null);
      setActiveNote(null);
      setActiveDocument(null);
    } else if (item.key === 'download') {
      setDownloadLog(true);
    }
    // else if (item.key === 'actions') {
    //   setActiveTab('tasks');
    //   router.replace(`/spaces/${currentSpace.slug}?t=tasks`);
    //   setActiveConversation(null);
    //   setActiveNote(null);
    //   setActiveDocument(null);
    // }
  };

  return (
    <StyledHeader>
      <AppSpaceHeaderMenus
        addNew={addNew}
        setAddNew={setAddNew}
        // breadcrumb={breadcrumb}
      />

      {isEditAccessAllowed(null, null, currentSpace) && (
        <Space size={0}>
          <Tooltip title={getAddButtonTooltip}>
            <AppHeaderButton
              type="text"
              shape="circle"
              size="small"
              icon={
                showCallIcon ? <MdCall size={22}/> : <MdAdd fontSize={22}/>
              }
              onClick={handleAddButtonClick}
            />
          </Tooltip>

          <Dropdown
            menu={{
              items: items,
              onClick: onMenuClick,
            }}
            placement="bottomRight"
            trigger={['click']}
          >
            <AppHeaderButton
              type="text"
              shape="circle"
              size="small"
              icon={<MdMoreVert fontSize={24}/>}
            />
          </Dropdown>
        </Space>
      )}

      <AppDrawer
        destroyOnClose
        isTabDrawer={true}
        title={formatMessage({id: 'space.edit'})}
        open={isEditOpen}
        destroyOnHidden={true}
        onClose={() => setEditOpen(false)}
        width={720}
        showLoader
      >
        {isEditOpen && <EditSpace onClose={() => setEditOpen(false)}/>}
      </AppDrawer>


      <AppDrawer
        open={isConfigureOpen}
        onClose={() => setIsConfigureOpen(false)}
        closable={false}
        title={formatMessage({id: 'space.linkAgent'})}
      >
        <ConfigureAgentModal
          currentSpace={currentSpace}
          $bodyHeight={170}
          onClose={() => setIsConfigureOpen(false)}
        />
      </AppDrawer>

      <AppDrawer
        title={formatMessage({id: 'drawer.downloadCallLogs'})}
        open={downloadLog}
        onClose={() => setDownloadLog(false)}
        width={600}
      >
        <DownloadLogs onClose={() => setDownloadLog(false)}/>
      </AppDrawer>

      <AppDrawer
        open={visible}
        onClose={() => setVisible(false)}
        closable={false}
        title={formatMessage({id: 'call.landingViewDrawerTitle'})}
        padding="0"
        extra={
          <AppHeaderButton
            type="primary"
            shape={!isMobile ? 'round' : 'circle'}
            icon={
              <span className="anticon" style={{verticalAlign: 'middle'}}>
                <MdCall fontSize={!isMobile ? 16 : 22}/>
              </span>
            }
            onClick={() => setCallModalOpen(true)}
          >
            {!isMobile && formatMessage({id: 'spaceHeader.callNow'})}
          </AppHeaderButton>
        }
      >
        <DocSelector allowSelection/>
      </AppDrawer>

      <AppSpaceCallModal
        open={isCallModalOpen}
        setOpen={setCallModalOpen}
        onFinishSchedule={(data) => {
          console.log('Call scheduled:', data);
          // Optionally refresh calls list or navigate
          setVisible(false);
        }}
        idKey="document_id"
      />
    </StyledHeader>
  );
};

export default SidebarHeader;
