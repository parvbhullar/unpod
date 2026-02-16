'use client';
import { useCallback, useEffect, useState } from 'react';
import {
  StyledDivider,
  StyledMainMenus,
  StyledMiniAvatar,
} from '@/core/AppLayout/MainLayout/LayoutSidebar/index.styled';
import { MdChecklist, MdOutlineCall, MdVoiceChat } from 'react-icons/md';
import AppLink from '@unpod/components/next/AppLink';
import { Tooltip } from 'antd';
import { useIntl } from 'react-intl';
import { RiChat3Line } from 'react-icons/ri';
import { usePathname } from 'next/navigation';
import {
  getDataApi,
  useAuthActionsContext,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { HiUserGroup } from 'react-icons/hi';
import { HiOutlineUsers } from 'react-icons/hi2';
import { TbBrandGoogleAnalytics } from 'react-icons/tb';
import type { Spaces } from '@unpod/constants/types';

const AIMenu = () => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const pathname = usePathname();
  const { activeOrg, isAuthenticated, user } = useAuthContext();
  const { formatMessage } = useIntl();
  const [spaceSlug, setSpaceSlug] = useState<string | undefined>(
    user?.active_space?.slug,
  );
  const [activeSpaceType, setActiveSpaceType] = useState<string | null>(
    user?.active_space?.content_type ?? null,
  );
  const { updateAuthUser } = useAuthActionsContext();

  const getLabel = (spaceType?: string | null) => {
    if (spaceType === 'contact') {
      return formatMessage({ id: 'nav.people' });
    } else if (spaceType === 'document') {
      return formatMessage({ id: 'nav.documents' });
    } else if (spaceType === 'email') {
      return formatMessage({ id: 'nav.inbox' });
    }
    return formatMessage({ id: 'nav.knowledge' });
  };

  const getIcon = (spaceType?: string | null) => {
    if (spaceType === 'contact') {
      return <HiOutlineUsers />;
    } else if (spaceType === 'document') {
      return <MdChecklist />;
    } else if (spaceType === 'email') {
      return <RiChat3Line />;
    }
    return <HiUserGroup />;
  };

  const getSpaces = useCallback(() => {
    (
      getDataApi(`spaces/`, infoViewActionsContext, {
        case: 'all',
      }) as Promise<{ data: Spaces[] }>
    )
      .then((response) => {
        if (!user?.active_space?.slug && response.data[0]) {
          updateAuthUser({
            ...user,
            active_space: response.data[0],
          });
          setSpaceSlug(response.data[0]?.slug);
        }
        // Response data can be used later if needed.
      })
      .catch((error: { message?: string }) => {
        infoViewActionsContext.showError(
          error.message || 'Failed to load spaces',
        );
      });
  }, [activeOrg]);

  useEffect(() => {
    if (isAuthenticated) {
      getSpaces();
      setActiveSpaceType(user?.active_space?.content_type ?? null);
      setSpaceSlug(user?.active_space?.slug);
    }
  }, [isAuthenticated, getSpaces, activeOrg?.domain_handle]);

  return (
    <StyledMainMenus orientation="vertical" align="center">
      <AppLink href={`/spaces/${spaceSlug}/chat/`}>
        <Tooltip placement="right" title={formatMessage({ id: 'nav.chat' })}>
          <StyledMiniAvatar
            icon={<MdVoiceChat />}
            className={
              pathname.includes(`spaces/${spaceSlug}/chat`) ? 'active' : ''
            }
          />
        </Tooltip>
      </AppLink>

      <AppLink href={`/spaces/${spaceSlug}/call/`} data-tour="calls">
        <Tooltip placement="right" title={formatMessage({ id: 'nav.calls' })}>
          <StyledMiniAvatar
            icon={<MdOutlineCall />}
            className={
              pathname.includes(`spaces/${spaceSlug}/call`) ? 'active' : ''
            }
          />
        </Tooltip>
      </AppLink>
      <AppLink href={`/spaces/${spaceSlug}/doc/`}>
        <Tooltip placement="right" title={getLabel(activeSpaceType)}>
          <StyledMiniAvatar
            icon={getIcon(activeSpaceType)}
            className={
              pathname.includes(`spaces/${spaceSlug}/doc`) ? 'active' : ''
            }
          />
        </Tooltip>
      </AppLink>
      {/* <AppLink href={`/spaces/${spaceSlug}/note/`}>
        <Tooltip placement="right" title={formatMessage({ id: 'nav.notes' })}>
          <StyledMiniAvatar
            icon={<VscChecklist />}
            className={
              pathname.includes(`spaces/${spaceSlug}/note`) ? 'active' : ''
            }
          />
        </Tooltip>
      </AppLink>*/}
      <StyledDivider />
      {/* <AppLink href={`/spaces/${spaceSlug}/logs/`}>
        <Tooltip placement="right" title={formatMessage({ id: 'nav.actionLogs' })}>
          <StyledMiniAvatar
            icon={<MdHistory />}
            className={
              pathname.includes(`spaces/${spaceSlug}/logs`) ? 'active' : ''
            }
          />
        </Tooltip>
      </AppLink>*/}
      <AppLink href={`/spaces/${spaceSlug}/analytics/`}>
        <Tooltip
          placement="right"
          title={formatMessage({ id: 'nav.analytics' })}
        >
          <StyledMiniAvatar
            icon={<TbBrandGoogleAnalytics />}
            className={
              pathname.includes(`spaces/${spaceSlug}/analytics`) ? 'active' : ''
            }
          />
        </Tooltip>
      </AppLink>
    </StyledMainMenus>
  );
};

export default AIMenu;
