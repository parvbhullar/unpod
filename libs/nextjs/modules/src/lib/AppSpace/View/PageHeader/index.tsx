import { Fragment, useEffect, useMemo, useState } from 'react';
import {
  getPostIcon,
  isEditAccessAllowed,
  isShareAccessAllowed,
} from '@unpod/helpers/PermissionHelper';
import { Badge, Dropdown, Modal } from 'antd';
import { MdDashboard, MdEdit, MdOutlineSettings } from 'react-icons/md';
import AppPageHeader, {
  AppHeaderButton,
} from '@unpod/components/common/AppPageHeader';
import {
  deleteDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useAuthContext,
  useInfoViewActionsContext,
  useOrgActionContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import PermissionPopover from '@unpod/components/common/PermissionPopover';
import { useMediaQuery } from 'react-responsive';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import AppSharedUsers from '@unpod/components/modules/AppSharedUsers';
import RequestPopover from '@unpod/components/common/RequestPopover';
import AppConnectorsSetting from '@unpod/components/modules/AppConnectorsSetting';
import AppConnectorList from '@unpod/components/modules/AppConnectorList';
import { AppDrawer } from '@unpod/components/antd';
import { SITE_URL, TabWidthQuery } from '@unpod/constants';
import SubscribeModal from './SubscribeModal';
import EditSpace from './EditSpace';
import { IconWrapper } from './index.styled';
import AppKbSchemaManager from '@unpod/components/modules/AppKbSchemaManager';
import { getKbInputsStructure } from '@unpod/helpers/AppKbHelper';
import { useIntl } from 'react-intl';

const PageHeader = ({ pageTitle }: { pageTitle?: any }) => {
  const { currentSpace, spaceSchema } = useAppSpaceContext();
  const { setCurrentSpace, setSpaceSchema } = useAppSpaceActionsContext();
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const infoViewActionsContext = useInfoViewActionsContext();
  const { setActiveSpace } = useOrgActionContext();
  const [openPermissionManager, setOpenPermissionManager] = useState(false);
  const [openRequestManager, setOpenRequestManager] = useState(false);
  const router = useRouter();
  const { isAuthenticated } = useAuthContext();
  const { formatMessage } = useIntl();
  const [isEditOpen, setEditOpen] = useState(false);
  const [isSchemaOpen, setSchemaOpen] = useState(false);
  const [userList, setUserList] = useState<any[]>([]);
  const [inputs, setInputs] = useState<any[]>([]);
  const [openConnectors, setOpenConnectors] = useState(false);

  useEffect(() => {
    if (spaceSchema) {
      const formInputs = getKbInputsStructure(spaceSchema);
      setInputs(formInputs as any[]);
    }
  }, [spaceSchema]);

  useEffect(() => {
    if (currentSpace?.users) {
      setUserList(
        currentSpace?.users.map((item: any) => ({
          ...item,
          email: item.email,
          role_code: item.role,
        })),
      );
    }
  }, [currentSpace?.users]);

  const items = useMemo(() => {
    const options = [
      {
        key: 'edit_space',
        label: 'Edit Space',
        icon: (
          <span className="ant-icon">
            <MdEdit fontSize={16} />
          </span>
        ),
      },
      {
        key: 'dashboard',
        label: 'Dashboard',
        icon: (
          <span className="ant-icon">
            <MdDashboard fontSize={16} />
          </span>
        ),
      },
    ];

    if (currentSpace?.content_type === 'contact') {
      options.push({
        key: 'edit_schema',
        label: 'Edit Schema',
        icon: (
          <span className="ant-icon">
            <MdEdit fontSize={16} />
          </span>
        ),
      });

      const schema = (currentSpace as any)?.schemas || {
        properties: undefined,
      };
      if (schema.properties) {
        const formInputs = getKbInputsStructure(schema);
        setInputs(formInputs as any[]);
      }
    }

    return options;
  }, [currentSpace]);

  const onMenuClick = (item: any) => {
    if (item.key === 'edit_space') {
      setEditOpen(true);
    } else if (item.key === 'edit_schema') {
      setSchemaOpen(true);
    } else if (item.key === 'archive-space') {
      confirmArchiveSpace();
    }
  };

  const getBtnText = () => {
    if (
      currentSpace?.final_role === ACCESS_ROLE.OWNER ||
      currentSpace?.final_role === ACCESS_ROLE.EDITOR
    ) {
      return 'Share';
    } else if (currentSpace?.final_role === ACCESS_ROLE.VIEWER) {
      return 'View Only';
    }

    return 'Subscribe';
  };

  const onArchiveSpace = () => {
    deleteDataApi(`spaces/${currentSpace?.slug}/`, infoViewActionsContext)
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        router.push(`/spaces/`);
      })
      .catch((error: any) => {
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

  const onSpaceUpdate = (newSpace: any) => {
    setCurrentSpace(newSpace);
    setActiveSpace(newSpace);
  };

  const [connector] = (currentSpace?.connected_apps || []) as any[];

  const PermissionPopoverAny = PermissionPopover as any;
  const RequestPopoverAny = RequestPopover as any;
  const AppSharedUsersAny = AppSharedUsers as any;

  return (
    <Fragment>
      <AppPageHeader
        hideToggleBtn
        hideAuthBtn={currentSpace?.privacy_type === 'public'}
        pageTitle={pageTitle || currentSpace?.name}
        isListingPage={!isAuthenticated}
        rightOptions={
          <Fragment>
            <AppSharedUsersAny users={userList} />

            {isAuthenticated &&
              !isTabletOrMobile &&
              (isShareAccessAllowed(null, null, currentSpace) ? (
                <PermissionPopoverAny
                  open={openPermissionManager}
                  onOpenChange={setOpenPermissionManager}
                  currentData={currentSpace}
                  setCurrentData={onSpaceUpdate}
                  userList={userList}
                  setUserList={setUserList}
                  linkShareable
                  type="space"
                >
                  <Badge count={(currentSpace?.access_request || []).length}>
                    <AppHeaderButton
                      type="primary"
                      shape="round"
                      icon={
                        <span
                          className={`anticon ${currentSpace?.privacy_type}-icon`}
                          style={{ verticalAlign: 'middle' }}
                        >
                          {getPostIcon(currentSpace?.privacy_type)}
                        </span>
                      }
                      onClick={() => setOpenPermissionManager(true)}
                    >
                      {getBtnText()}
                    </AppHeaderButton>
                  </Badge>
                </PermissionPopoverAny>
              ) : (
                <RequestPopoverAny
                  open={openRequestManager}
                  onOpenChange={setOpenRequestManager}
                  currentData={currentSpace}
                  setCurrentData={onSpaceUpdate}
                  title={formatMessage({ id: 'common.requestAccess' })}
                  type="space"
                >
                  <AppHeaderButton
                    type="primary"
                    shape="round"
                    icon={
                      <span
                        className={`anticon ${currentSpace?.privacy_type}-icon`}
                        style={{ verticalAlign: 'middle' }}
                      >
                        {getPostIcon(currentSpace?.privacy_type)}
                      </span>
                    }
                    onClick={() => setOpenRequestManager(true)}
                  >
                    {getBtnText()}
                  </AppHeaderButton>
                </RequestPopoverAny>
              ))}

            {!isAuthenticated &&
              currentSpace?.token &&
              currentSpace?.privacy_type === 'public' && (
                <SubscribeModal currentSpace={currentSpace} />
              )}

            {currentSpace?.content_type === 'email' &&
              (connector ? (
                <AppConnectorsSetting
                  data={currentSpace}
                  setData={onSpaceUpdate}
                />
              ) : (
                <AppHeaderButton
                  type="primary"
                  shape="round"
                  onClick={() => setOpenConnectors(true)}
                  ghost
                >
                  Connect
                </AppHeaderButton>
              ))}

            {isEditAccessAllowed(null, null, currentSpace) && (
              <Dropdown
                menu={{
                  items: items,
                  onClick: onMenuClick,
                }}
                placement="bottomRight"
                trigger={['click']}
              >
                <IconWrapper>
                  <MdOutlineSettings fontSize={24} />
                </IconWrapper>
              </Dropdown>
            )}
          </Fragment>
        }
      />

      <AppDrawer
        title="Connect"
        open={openConnectors}
        onClose={() => setOpenConnectors(false)}
        width={560}
      >
        <AppConnectorList
          defaultPayload={{
            redirect_route: `${SITE_URL}/spaces/${currentSpace?.slug}/`,
            space: currentSpace?.slug,
          }}
        />
      </AppDrawer>

      <Modal
        title="Update Space"
        footer={null}
        open={isEditOpen}
        destroyOnHidden={true}
        onCancel={() => setEditOpen(false)}
      >
        {isEditOpen && (
          <EditSpace
            currentSpace={currentSpace}
            setCurrentSpace={setCurrentSpace}
            onClose={() => setEditOpen(false)}
          />
        )}
      </Modal>

      <AppDrawer
        title="Manage Schema"
        open={isSchemaOpen}
        destroyOnHidden={true}
        onClose={() => setSchemaOpen(false)}
        width={720}
        showLoader
      >
        {isSchemaOpen && (
          <AppKbSchemaManager
            title="Schema"
            currentKb={currentSpace}
            inputs={inputs}
            setInputs={setInputs}
            onClose={() => setSchemaOpen(false)}
            setSpaceSchema={setSpaceSchema}
          />
        )}
      </AppDrawer>
    </Fragment>
  );
};

export default PageHeader;
