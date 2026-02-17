'use client';
import { memo, useMemo } from 'react';
import {
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppLink from '@unpod/components/next/AppLink';
import { MdLogout, MdOutlineAccountBalanceWallet } from 'react-icons/md';
import { StyledUserAvatar, UserInfoWrapper } from './index.styled';
import { usePathname } from 'next/navigation';
import { Dropdown, type MenuProps } from 'antd';
import UserAvatar from '@unpod/components/common/UserAvatar';
import { TbCalendarDollar } from 'react-icons/tb';
import useIsDesktop from '@unpod/custom-hooks/useIsDesktop';
import { useIntl } from 'react-intl';
import type { User } from '@unpod/constants/types';

function getItem(
  label: string | undefined,
  key: string,
  icon: JSX.Element,
  path?: string,
): NonNullable<MenuProps['items']>[number] {
  return {
    key,
    icon,
    label: path ? <AppLink href={path}>{label || ''}</AppLink> : label || '',
  };
}

const UserInfo = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { logoutUser } = useAuthActionsContext();
  const { user } = useAuthContext();
  const pathname = usePathname();
  const { isDesktopApp } = useIsDesktop();
  const { formatMessage } = useIntl();

  const items = useMemo<MenuProps['items']>(() => {
    const baseItems = [
      getItem(
        user?.full_name,
        'profile',
        <span>
          <UserAvatar
            user={
              {
                ...(user || {}),
                ...(user?.user_detail || {}),
                profile_color: user?.user_detail?.profile_color ?? undefined,
                profile_picture:
                  user?.user_detail?.profile_picture ?? undefined,
              } satisfies User
            }
            size={20}
          />
        </span>,
        '/profile/',
      ),
      getItem(
        formatMessage({ id: 'nav.signOut' }),
        'logout',
        <MdLogout style={{ fontSize: 16 }} />,
      ),
    ];
    return baseItems.filter(Boolean) as MenuProps['items'];
  }, [user]);

  const onUserMenuClick: MenuProps['onClick'] = (options) => {
    if (options.key === 'logout') {
      (logoutUser() as Promise<{ message?: string }>)
        .then((response) => {
          infoViewActionsContext.showMessage(response.message || 'Logged out');
          if (isDesktopApp) window.location.href = '/auth/signin';
          else window.location.href = '/';
        })
        .catch((response: { message?: string }) => {
          infoViewActionsContext.showError(response.message || 'Logout failed');
        });
    }
  };

  return (
    <Dropdown
      menu={{ items, onClick: onUserMenuClick }}
      placement="top"
      trigger={['hover']}
    >
      <UserInfoWrapper
        className="ant-dropdown-link user-profile"
        onClick={(e) => e.preventDefault()}
        data-tour="profile"
      >
        <StyledUserAvatar
          user={{
            ...(user || {}),
            ...(user?.user_detail || {}),
            profile_color: user?.user_detail?.profile_color ?? undefined,
            profile_picture: user?.user_detail?.profile_picture ?? undefined,
          }}
          size={42}
          shape="square"
          className={pathname === '/profile' ? 'active' : ''}
        />
      </UserInfoWrapper>
    </Dropdown>
  );
};

export default memo(UserInfo);
