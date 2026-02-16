'use client';
import AppLink from '@unpod/components/next/AppLink';
import { Tooltip } from 'antd';
import {
  StyledMainMenus,
  StyledMiniAvatar,
} from '@/core/AppLayout/MainLayout/LayoutSidebar/index.styled';
import { MdOutlinePhone } from 'react-icons/md';
import { RiDashboardHorizontalLine, RiRobot2Line } from 'react-icons/ri';
import { BsDatabase } from 'react-icons/bs';
import { usePathname } from 'next/navigation';
import { useAuthContext } from '@unpod/providers';
import { useIntl } from 'react-intl';

type SipMenuProps = {
  onClickMenu: (path: string) => void;
};

const SipMenu = ({ onClickMenu }: SipMenuProps) => {
  const pathname = usePathname();
  const { formatMessage } = useIntl();
  const { subscription } = useAuthContext();
  const allowedModules = (subscription as { allowed_modules?: string[] } | null)
    ?.allowed_modules;

  return (
    <StyledMainMenus orientation="vertical" align="center">
      <AppLink href="/org">
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
      {allowedModules?.includes('channels') && (
        <AppLink href="/bridges">
          <Tooltip
            placement="right"
            title={formatMessage({ id: 'nav.telephony' })}
          >
            <StyledMiniAvatar
              icon={<MdOutlinePhone fontSize={21} />}
              onClick={() => onClickMenu('/bridges')}
              className={
                pathname.startsWith('/bridges/') &&
                pathname !== '/bridges/audit/'
                  ? 'active'
                  : ''
              }
            />
          </Tooltip>
        </AppLink>
      )}
      <AppLink href="/ai-studio">
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
      <AppLink href="/knowledge-bases">
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
    </StyledMainMenus>
  );
};

export default SipMenu;
