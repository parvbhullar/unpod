import {Fragment, useEffect, useState} from 'react';
import AppLink from '@unpod/components/next/AppLink';
import {MdOutlineWorkspaces} from 'react-icons/md';
import {useMediaQuery} from 'react-responsive';
import {Badge} from 'antd';
import AppPageHeader, {AppHeaderButton,} from '@unpod/components/common/AppPageHeader';
import {AppBreadCrumb, AppBreadCrumbTitle} from '@unpod/components/antd';
import {useAuthContext} from '@unpod/providers';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import AppSharedUsers from '@unpod/components/modules/AppSharedUsers';
import {getPostIcon, isShareBtnAccessAllowed,} from '@unpod/helpers/PermissionHelper';
import PermissionPopover from '@unpod/components/common/PermissionPopover';
import RequestPopover from '@unpod/components/common/RequestPopover';
import {StyledMainTitle, StyledTitleBlock, StyledTitleWrapper,} from './index.styled';
import {TabWidthQuery} from '@unpod/constants';
import {useIntl} from 'react-intl';

type PageHeaderProps = {
  currentPost: any;
  setCurrentPost: (post: any) => void;
};

const PageHeader = ({currentPost, setCurrentPost}: PageHeaderProps) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const {isAuthenticated} = useAuthContext();
  const [openPermissionManager, setOpenPermissionManager] = useState(false);
  const [openRequestManager, setOpenRequestManager] = useState(false);
  const [userList, setUserList] = useState<any[]>([]);
  const {formatMessage} = useIntl();

  const items = [
    {
      title: (
        <AppLink href={`/${currentPost?.organization?.domain_handle}/org`}>
          {formatMessage({id: 'common.home'})}
        </AppLink>
      ),
    },
    {
      title: (
        <AppLink href={`/spaces/${currentPost?.space?.slug}`}>
          <AppBreadCrumbTitle
            title={
              currentPost?.space?.name || formatMessage({id: 'space.space'})
            }
          />
        </AppLink>
      ),
    },
    {
      title: <AppBreadCrumbTitle title={currentPost?.title}/>,
    },
  ];

  useEffect(() => {
    setUserList(
      currentPost?.users?.map((item: any) => ({
        ...item,
        email: item.email,
        role_code: item.role,
      })),
    );
  }, [currentPost?.users]);

  const getBtnText = () => {
    if (
      currentPost?.final_role === ACCESS_ROLE.OWNER ||
      currentPost?.final_role === ACCESS_ROLE.EDITOR
    ) {
      return formatMessage({id: 'common.share'});
    } else if (currentPost?.final_role === ACCESS_ROLE.VIEWER) {
      return formatMessage({id: 'common.viewOnly'});
    }

    return formatMessage({id: 'common.subscribe'});
  };

  return (
    <AppPageHeader
      hideToggleBtn
      pageTitle={
        <StyledTitleBlock>
          <MdOutlineWorkspaces fontSize={21}/>
          <StyledTitleWrapper>
            <StyledMainTitle ellipsis={{rows: 1}}>
              {currentPost?.space?.name || formatMessage({id: 'space.space'})}
            </StyledMainTitle>

            <AppBreadCrumb items={items}/>
          </StyledTitleWrapper>
        </StyledTitleBlock>
      }
      rightOptions={
        <Fragment>
          <AppSharedUsers users={userList}/>
          {isAuthenticated &&
            !isTabletOrMobile &&
            (isShareBtnAccessAllowed(null, currentPost, null) ? (
              <PermissionPopover
                open={openPermissionManager}
                onOpenChange={setOpenPermissionManager}
                title={formatMessage({id: 'common.share'})}
                placement="bottomRight"
                currentData={currentPost}
                setCurrentData={setCurrentPost}
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
                        style={{verticalAlign: 'middle'}}
                      >
                        {getPostIcon(currentPost?.privacy_type)}
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
                currentData={currentPost}
                setCurrentData={setCurrentPost}
                title={formatMessage({id: 'common.requestAccess'})}
                placement="bottomRight"
                type="post"
              >
                <AppHeaderButton
                  type="primary"
                  shape="round"
                  icon={
                    <span
                      className="anticon"
                      style={{verticalAlign: 'middle'}}
                    >
                      {getPostIcon(currentPost?.privacy_type)}
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
