'use client';
import {useEffect, useState} from 'react';
import {MdHistory, MdKey, MdLockOpen, MdOutlineWorkspaces,} from 'react-icons/md';
import {Popover, Tooltip} from 'antd';
import {useAuthContext} from '@unpod/providers';
import {useParams, usePathname, useRouter} from 'next/navigation';
import AppLink from '@unpod/components/next/AppLink';
import clsx from 'clsx';
import {getFirstLetter} from '@unpod/helpers/StringHelper';
import Notification from '../Notification';
import UserInfo from './UserInfo';
import {isEmptyObject} from '@unpod/helpers/GlobalHelper';
import HubSelectionList from './HubSelectionList';
import {
  StyledInnerContainer,
  StyledMainMenus,
  StyledMiniAvatar,
  StyledMinibar,
  StyledMiniLogo,
  StyledScrollbar,
  StyledUserMenus,
} from './index.styled';
import AIMenu from '@/core/AppLayout/MainLayout/LayoutSidebar/AIMenu';
import DrawerMenu from '@/core/AppLayout/MainLayout/LayoutSidebar/DrawerMenu';
import AdminMenu from '@/core/AppLayout/MainLayout/LayoutSidebar/AdminMenu';
import {RiRobot2Line} from 'react-icons/ri';
import useIsDesktop from '@unpod/custom-hooks/useIsDesktop';
import {useIntl} from 'react-intl';
import type {Organization, User} from '@unpod/constants/types';

const LayoutSidebar = () => {
  const [openOrgMenu, setOpenOrgMenu] = useState(false);

  const router = useRouter();
  const params = useParams() as { orgSlug?: string };
  const pathname = usePathname();

  const validPageUrl = ['doc', 'call', 'chat', 'ai-studio', 'bridges'];

  const segments = pathname.split('/').filter(Boolean);
  const sideBar = segments.find((seg) => validPageUrl.includes(seg));

  const { orgSlug } = params;

  const { isAuthenticated, user, activeOrg } = useAuthContext();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);


  useEffect(() => {
    if (pathname && isAuthenticated) {
      // Admin/Studio paths that should show AdminMenu
      const adminPaths = [
        '/org',
        '/ai-studio',
        '/knowledge-bases',
        '/call-logs',
        '/api-keys',
      ];
      const isAdminPath = adminPaths.some((path) => pathname.startsWith(path));
      if (isAdminPath !== isSettingsOpen&& process.env.productId === 'unpod.ai' ) setIsSettingsOpen(isAdminPath);
    }
  }, [pathname, isAuthenticated]);

  const onClickMenu = (path: string) => {
    if (path !== pathname) {
      router.push(path);
    }
  };

  return (
    <StyledMinibar>
      <StyledInnerContainer>
        <StyledScrollbar>
          {isSettingsOpen ? (
            <AdminMenus
              orgSlug={orgSlug}
              onClickMenu={onClickMenu}
              setOpenOrgMenu={setOpenOrgMenu}
              openOrgMenu={openOrgMenu}
              sideBar={sideBar}
            />
          ) : (
            <UserMainMenu
              user={user}
              isAuthenticated={isAuthenticated}
              openOrgMenu={openOrgMenu}
              activeOrg={activeOrg}
              orgSlug={orgSlug}
              setOpenOrgMenu={setOpenOrgMenu}
              onClickMenu={onClickMenu}
              sideBar={sideBar}
            />
          )}
          <UserMenus
            isAuthenticated={isAuthenticated}
            isSettingsOpen={isSettingsOpen}
            setIsSettingsOpen={setIsSettingsOpen}
          />
        </StyledScrollbar>
      </StyledInnerContainer>
    </StyledMinibar>
  );
};

export default LayoutSidebar;

type AdminMenusProps = {
  orgSlug?: string;
  onClickMenu: (path: string) => void;
  openOrgMenu: boolean;
  setOpenOrgMenu: (open: boolean) => void;
  sideBar?: string;
};

const AdminMenus = ({
  orgSlug,
  onClickMenu,
  openOrgMenu,
  setOpenOrgMenu,
  sideBar,
}: AdminMenusProps) => {
  const { activeOrg, user, isAuthenticated } = useAuthContext();

  return (
    <StyledMainMenus orientation="vertical" align="center">
      {sideBar && <DrawerMenu />}
      {isAuthenticated ? (
        <Popover
          open={openOrgMenu}
          onOpenChange={(visible) => setOpenOrgMenu(visible)}
          content={<HubSelectionList setOpenOrgMenu={setOpenOrgMenu} />}
          trigger="click"
          placement="rightTop"
        >
          <StyledMiniAvatar
            className={clsx('org-avatar partially-active', {
              'placeholder-avatar': !activeOrg?.logo,
              active: orgSlug === activeOrg?.domain_handle,
            })}
            $avatarColor={activeOrg?.logo ? '' : activeOrg?.color}
            $isLogo={Boolean(activeOrg?.logo)}
            src={activeOrg?.logo}
            shape="square"
          >
            {getFirstLetter(
              activeOrg?.name ||
                (isEmptyObject(user?.organization ?? {}) ? 'CH' : 'JH'),
            )}
          </StyledMiniAvatar>
        </Popover>
      ) : (
        <AppLink href="/">
          <StyledMiniAvatar
            src="/images/unpod/logo-icon.svg"
            alt="unpod-logo"
            $isAppLogo
            $isLogo
          />
        </AppLink>
      )}
      {isAuthenticated && activeOrg && <AdminMenu onClickMenu={onClickMenu} />}
    </StyledMainMenus>
  );
};

type UserMainMenuProps = {
  isAuthenticated: boolean;
  openOrgMenu: boolean;
  activeOrg: Organization | null;
  setOpenOrgMenu: (open: boolean) => void;
  user: User | null;
  orgSlug?: string;
  onClickMenu: (path: string) => void;
  sideBar?: string;
};

const UserMainMenu = ({
  isAuthenticated,
  openOrgMenu,
  activeOrg,
  setOpenOrgMenu,
  user,
  orgSlug,
  onClickMenu,
  sideBar,
}: UserMainMenuProps) => {
  return (
    <StyledMainMenus orientation="vertical" align="center">
      {sideBar && <DrawerMenu />}
      {isAuthenticated ? (
        <Popover
          open={openOrgMenu}
          onOpenChange={(visible) => setOpenOrgMenu(visible)}
          content={<HubSelectionList setOpenOrgMenu={setOpenOrgMenu} />}
          trigger="click"
          placement="rightTop"
        >
          <StyledMiniAvatar
            className={clsx('org-avatar partially-active', {
              'placeholder-avatar': !activeOrg?.logo,
              active: orgSlug === activeOrg?.domain_handle,
            })}
            $avatarColor={activeOrg?.logo ? '' : activeOrg?.color}
            $isLogo={Boolean(activeOrg?.logo)}
            src={activeOrg?.logo}
            shape="square"
          >
            {getFirstLetter(
              activeOrg?.name ||
                (isEmptyObject(user?.organization ?? {}) ? 'CH' : 'JH'),
            )}
          </StyledMiniAvatar>
        </Popover>
      ) : (
        <AppLink href="/">
          <StyledMiniAvatar
            src="/images/unpod/logo-icon.svg"
            alt="unpod-logo"
            $isAppLogo
            $isLogo
          />
        </AppLink>
      )}
      {isAuthenticated &&
        activeOrg?.domain_handle &&
        <AIMenu/>
      }
    </StyledMainMenus>
  );
};

type UserMenusProps = {
  isAuthenticated: boolean;
  isSettingsOpen: boolean;
  setIsSettingsOpen: (open: boolean) => void;
};

const UserMenus = ({
  isAuthenticated,
  isSettingsOpen,
  setIsSettingsOpen,
}: UserMenusProps) => {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuthContext();
  const spaceSlug = user?.active_space?.slug;
  const { isDesktopApp } = useIsDesktop();
  const { formatMessage } = useIntl();

  return (
    <StyledUserMenus orientation="vertical">
      {isAuthenticated ? (
        <>
          {process.env.productId === 'unpod.dev' ? (
            <>
              <AppLink href="/call-logs">
                <Tooltip
                  placement="right"
                  title={formatMessage({ id: 'nav.callLogs' })}
                >
                  <StyledMiniAvatar
                    icon={<MdHistory fontSize={18} />}
                    className={clsx({
                      active: pathname === '/call-logs/',
                    })}
                  />
                </Tooltip>
              </AppLink>
              <AppLink href="/api-keys">
                <Tooltip
                  placement="right"
                  title={formatMessage({ id: 'nav.apiKeys' })}
                >
                  <StyledMiniAvatar
                    icon={<MdKey fontSize={18} />}
                    className={clsx({
                      active: pathname === '/api-keys/',
                    })}
                  />
                </Tooltip>
              </AppLink>
            </>
          ) : (
            <Tooltip
              placement="top"
              title={
                isSettingsOpen
                  ? formatMessage({ id: 'nav.spaceView' })
                  : formatMessage({ id: 'nav.studioView' })
              }
            >
              <StyledMiniAvatar
                onClick={() => {
                  if (isSettingsOpen) {
                    router.push(`/spaces/${spaceSlug}/call/`);
                  } else {
                    router.push(`/org/`);
                  }
                  setIsSettingsOpen(!isSettingsOpen);
                }}
                icon={
                  isSettingsOpen ? (
                    <MdOutlineWorkspaces fontSize={21} />
                  ) : (
                    <RiRobot2Line fontSize={22} />
                  )
                }
                style={{ marginBottom: -6 }}
                className="studio-view-toggle"
                data-tour="studio-view"
              />
            </Tooltip>
          )}
          {isAuthenticated && <Notification />}
          <UserInfo />
          {isDesktopApp ? null : (
            <AppLink href="/">
              <StyledMiniLogo
                src="/images/unpod/logo-icon.svg"
                alt="unpod-logo"
                $isAppLogo
              />
            </AppLink>
          )}
        </>
      ) : (
        <AppLink href="/auth/signin/">
          <Tooltip
            placement="right"
            title={formatMessage({ id: 'auth.signIn' })}
          >
            <StyledMiniAvatar icon={<MdLockOpen fontSize={18} />} />
          </Tooltip>
        </AppLink>
      )}
    </StyledUserMenus>
  );
};
