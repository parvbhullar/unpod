'use client';
import AppLink from '@unpod/components/next/AppLink';
import { Tooltip } from 'antd';
import { useIntl } from 'react-intl';
import {
  StyledMainMenus,
  StyledMiniAvatar,
} from '@/core/AppLayout/MainLayout/LayoutSidebar/index.styled';
import { MdHistory, MdKey } from 'react-icons/md';
import { RiDashboardHorizontalLine, RiRobot2Line } from 'react-icons/ri';
import { BsDatabase } from 'react-icons/bs';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { useIsDesktop } from '@unpod/custom-hooks';

type AdminMenuProps = {
  onClickMenu: (path: string) => void;
};

const AdminMenu = ({ onClickMenu }: AdminMenuProps) => {
  const pathname = usePathname();
  const { isDesktopApp } = useIsDesktop();
  const { formatMessage } = useIntl();
  return (
    <StyledMainMenus orientation="vertical" align="center">
      <AppLink href="/org" data-tour="admin-dashboard">
        <Tooltip
          placement="right"
          title={formatMessage({ id: 'nav.dashboard' })}
        >
          <StyledMiniAvatar
            icon={<RiDashboardHorizontalLine fontSize={21} />}
            className={pathname.includes('/org') ? 'active' : ''}
          />
        </Tooltip>
      </AppLink>
      <AppLink href="/ai-studio" data-tour="admin-ai-studio">
        <Tooltip
          placement="right"
          title={formatMessage({ id: 'nav.aiStudio' })}
        >
          <StyledMiniAvatar
            icon={<RiRobot2Line fontSize={21} />}
            className={
              pathname.includes('ai-studio') && pathname !== '/ai-studio/new'
                ? 'active'
                : ''
            }
          />
        </Tooltip>
      </AppLink>
      <AppLink href="/knowledge-bases" data-tour="admin-knowledge-bases">
        <Tooltip
          placement="right"
          title={formatMessage({ id: 'nav.knowledgeBase' })}
        >
          <StyledMiniAvatar
            icon={<BsDatabase fontSize={21} />}
            onClick={() => onClickMenu('/knowledge-bases')}
            className={pathname.startsWith('/knowledge-bases/') ? 'active' : ''}
          />
        </Tooltip>
      </AppLink>

      {!isDesktopApp && (
        <AppLink href="/call-logs" data-tour="admin-call-logs">
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
      )}
      <AppLink href="/api-keys" data-tour="admin-api-keys">
        <Tooltip placement="right" title={formatMessage({ id: 'nav.apiKeys' })}>
          <StyledMiniAvatar
            icon={<MdKey fontSize={18} />}
            className={clsx({
              active: pathname === '/api-keys/',
            })}
          />
        </Tooltip>
      </AppLink>
    </StyledMainMenus>
  );
};

export default AdminMenu;
