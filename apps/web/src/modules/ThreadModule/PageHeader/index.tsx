import type { Dispatch, SetStateAction } from 'react';
import type { Thread } from '@unpod/constants/types';

import { Fragment, useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useMediaQuery } from 'react-responsive';
import { Badge } from 'antd';
import { MdOutlineWorkspaces } from 'react-icons/md';

import { TabWidthQuery } from '@unpod/constants';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import { useAuthContext } from '@unpod/providers';
import { getPostIcon, isShareBtnAccessAllowed } from '@unpod/helpers/PermissionHelper';
import { AppBreadCrumb, AppBreadCrumbTitle } from '@unpod/components/antd';
import AppLink from '@unpod/components/next/AppLink';
import AppSharedUsers from '@unpod/components/modules/AppSharedUsers';
import PermissionPopover from '@unpod/components/common/PermissionPopover';
import RequestPopover from '@unpod/components/common/RequestPopover';
import AppPageHeader, { AppHeaderButton } from '@unpod/components/common/AppPageHeader';

import {
  StyledMainTitle,
  StyledTitleBlock,
  StyledTitleWrapper,
} from './index.styled';

type PageHeaderProps = {
  currentPost: Thread | null;
  setCurrentPost: Dispatch<SetStateAction<Thread | null>>;
};

type PostUser = NonNullable<Thread['users']>[number];

const PageHeader = ({ currentPost, setCurrentPost }: PageHeaderProps) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const { isAuthenticated } = useAuthContext();
  const { formatMessage } = useIntl();
  const [openPermissionManager, setOpenPermissionManager] = useState(false);
  const [openRequestManager, setOpenRequestManager] = useState(false);
  const [userList, setUserList] = useState<PostUser[]>([]);

  const items = [
    {
      title: (
        <AppLink href={`/${currentPost?.organization?.domain_handle}/org`}>
          Home
        </AppLink>
      ),
    },
    {
      title: (
        <AppLink href={`/spaces/${currentPost?.space?.slug}`}>
          <AppBreadCrumbTitle title={currentPost?.space?.name || 'Space'} />
        </AppLink>
      ),
    },
    {
      title: <AppBreadCrumbTitle title={currentPost?.title || ''} />,
    },
  ];

  useEffect(() => {
    setUserList(
      currentPost?.users?.map((item) => ({
        ...item,
        email: item.email,
        role_code: item.role,
      })) ?? [],
    );
  }, [currentPost?.users]);

  const getBtnText = () => {
    if (
      currentPost?.final_role === ACCESS_ROLE.OWNER ||
      currentPost?.final_role === ACCESS_ROLE.EDITOR
    ) {
      return 'Share';
    } else if (currentPost?.final_role === ACCESS_ROLE.VIEWER) {
      return 'View Only';
    }

    return 'Subscribe';
  };

  return (
    <AppPageHeader
      hideToggleBtn
      pageTitle={
        <StyledTitleBlock>
          <MdOutlineWorkspaces fontSize={21} />
          <StyledTitleWrapper>
            <StyledMainTitle ellipsis={{ rows: 1 }}>
              {currentPost?.space?.name || 'Space'}
            </StyledMainTitle>

            <AppBreadCrumb items={items} />
          </StyledTitleWrapper>
        </StyledTitleBlock>
      }
      rightOptions={
        <Fragment>
          <AppSharedUsers users={userList} />
          {isAuthenticated &&
            !isTabletOrMobile &&
            (isShareBtnAccessAllowed(null, currentPost, null) ? (
              <PermissionPopover
                open={openPermissionManager}
                onOpenChange={setOpenPermissionManager}
                type="thread"
                title={formatMessage({ id: 'permissionPopover.defaultTitle' })}
                placement="bottomRight"
                currentData={currentPost ?? {}}
                setCurrentData={(data: Thread) => setCurrentPost(data)}
                userList={userList}
                setUserList={setUserList}
                linkShareable
              >
                <Badge count={(currentPost?.access_request || []).length}>
                  <AppHeaderButton
                    type="primary"
                    shape="round"
                    icon={
                      <span
                        className="anticon"
                        style={{ verticalAlign: 'middle' }}
                      >
                        {getPostIcon(currentPost?.privacy_type ?? 'public')}
                      </span>
                    }
                    onClick={() => setOpenPermissionManager(true)}
                  >
                    {getBtnText()}
                  </AppHeaderButton>
                </Badge>
              </PermissionPopover>
            ) : (
              <RequestPopover
                open={openRequestManager}
                onOpenChange={setOpenRequestManager}
                type="thread"
                currentData={currentPost ?? {}}
                setCurrentData={(data: Thread) => setCurrentPost(data)}
                title={formatMessage({ id: 'common.requestAccess' })}
              >
                <AppHeaderButton
                  type="primary"
                  shape="round"
                  icon={
                    <span
                      className="anticon"
                      style={{ verticalAlign: 'middle' }}
                    >
                      {getPostIcon(currentPost?.privacy_type ?? 'public')}
                    </span>
                  }
                  onClick={() => setOpenRequestManager(true)}
                >
                  {getBtnText()}
                </AppHeaderButton>
              </RequestPopover>
            ))}
        </Fragment>
      }
    />
  );
};

export default PageHeader;
