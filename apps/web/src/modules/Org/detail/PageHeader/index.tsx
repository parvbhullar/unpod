import React, { Fragment, useState } from 'react';
import {
  getPostIcon,
  isEditAccessAllowed,
} from '@unpod/helpers/PermissionHelper';
import PermissionPopover from '@unpod/components/common/PermissionPopover';
import { Badge, Dropdown } from 'antd';
import { IconWrapper } from './index.styled';
import { useMediaQuery } from 'react-responsive';
import { useAuthActionsContext, useAuthContext } from '@unpod/providers';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import { MdOutlineSettings } from 'react-icons/md';
import { useRouter } from 'next/navigation';
import AppSharedUsers from '@unpod/components/modules/AppSharedUsers';
import RequestPopover from '@unpod/components/common/RequestPopover';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import AppPageHeader, {
  AppHeaderButton,
} from '@unpod/components/common/AppPageHeader';
import { TabWidthQuery } from '@unpod/constants';
import AppCopyToClipboard from '@unpod/components/third-party/AppCopyToClipboard';
import { useIntl } from 'react-intl';
import type { Organization } from '@unpod/constants/types';
import { PermissionPopoverType } from '@unpod/components/common/PermissionPopover/types';

type PageHeaderProps = {
  type?: PermissionPopoverType;
  pageTitle?: React.ReactNode;
  isListingPage?: boolean;
};

const PageHeader: React.FC<PageHeaderProps> = ({
  type,
  pageTitle,
  isListingPage,
}) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const router = useRouter();
  const { isAuthenticated, activeOrg } = useAuthContext();
  const { setActiveOrg } = useAuthActionsContext();
  const [openPermissionManager, setOpenPermissionManager] = useState(false);
  const [openRequestManager, setOpenRequestManager] = useState(false);
  const [addNew, setAddNew] = useState(false);
  const { formatMessage } = useIntl();

  const getBtnText = () => {
    if (
      activeOrg?.final_role === ACCESS_ROLE.OWNER ||
      activeOrg?.final_role === ACCESS_ROLE.EDITOR
    ) {
      return 'common.share';
    } else if (activeOrg?.final_role === ACCESS_ROLE.VIEWER) {
      return 'common.viewOnly';
    }
    return activeOrg?.privacy_type === 'public'
      ? 'common.join'
      : 'common.subscribe';
  };

  const onUpdateOrg = (data: Organization) => {
    setActiveOrg(data);
  };

  return (
    <AppPageHeader
      hideToggleBtn
      pageTitle={
        pageTitle || (
          <AppSpaceHeaderMenus addNew={addNew} setAddNew={setAddNew} />
        )
      }
      rightOptions={
        <Fragment>
          {Boolean(activeOrg?.joined) && (
            <AppSharedUsers
              users={activeOrg?.users?.map((item) => ({
                ...item,
                email: item.email,
                role_code: item.role,
              }))}
            />
          )}

          {isAuthenticated &&
            activeOrg &&
            !isTabletOrMobile &&
            (isEditAccessAllowed(activeOrg, undefined, undefined) ? (
              <PermissionPopover
                currentData={activeOrg as any}
                setCurrentData={onUpdateOrg as any}
                open={openPermissionManager}
                onOpenChange={setOpenPermissionManager}
                linkShareable
                type={type || 'org'}
                title={formatMessage({ id: 'permissionPopover.orgTitle' })}
                placement="bottomLeft"
              >
                <Badge count={(activeOrg?.access_request || []).length}>
                  <AppHeaderButton
                    type="primary"
                    shape="round"
                    icon={
                      <span
                        className="anticon"
                        style={{ verticalAlign: 'middle' }}
                      >
                        {getPostIcon(String(activeOrg?.privacy_type || ''))}
                      </span>
                    }
                    onClick={() => setOpenPermissionManager(true)}
                  >
                    {formatMessage({ id: getBtnText() })}
                  </AppHeaderButton>
                </Badge>
              </PermissionPopover>
            ) : (
              <RequestPopover
                type="org"
                open={openRequestManager}
                onOpenChange={setOpenRequestManager}
                currentData={activeOrg as any}
                setCurrentData={onUpdateOrg as any}
                title={formatMessage({ id: 'common.requestAccess' })}
                placement="bottomLeft"
              >
                <AppHeaderButton
                  type="primary"
                  shape="round"
                  icon={
                    <span
                      className="anticon"
                      style={{ verticalAlign: 'middle' }}
                    >
                      {getPostIcon(String(activeOrg?.privacy_type || ''))}
                    </span>
                  }
                  onClick={() => setOpenRequestManager(true)}
                >
                  {formatMessage({ id: getBtnText() })}
                </AppHeaderButton>
              </RequestPopover>
            ))}

          {isEditAccessAllowed(activeOrg, undefined, undefined) && (
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'hub_settings',
                    label: formatMessage({ id: 'common.settings' }),
                  },
                  {
                    key: 'org_handle',
                    label: (
                      <AppCopyToClipboard
                        title={formatMessage({ id: 'dropdown.copyOrgHandle' })}
                        text={activeOrg?.domain_handle || ''}
                        hideIcon={false}
                      />
                    ),
                  },
                ],
                onClick: (item) => {
                  if (item.key === 'hub_settings') {
                    router.push(`/org/settings`);
                  }
                },
              }}
              placement="bottomLeft"
              trigger={['click']}
            >
              <IconWrapper>
                <MdOutlineSettings fontSize={24} />
              </IconWrapper>
            </Dropdown>
          )}
        </Fragment>
      }
      /*rightOptions={
        isEditAccessAllowed(activeOrg, undefined, undefined) && (
          <Dropdown
            menu={{
              items: [
                {
                  key: 'hub_settings',
                  label: 'Organization Settings',
                },
              ],
              onClick: (item) => {
                if (item.key === 'hub_settings') {
                  router.push(`/${activeOrg.domain_handle}/org/settings`);
                }
              },
            }}
            placement="bottomLeft"
            trigger={['click']}
          >
            <IconWrapper>
              <MdOutlineSettings fontSize={24} />
            </IconWrapper>
          </Dropdown>
        )
      }*/
      isListingPage={isListingPage}
    />
  );
};

export default PageHeader;
