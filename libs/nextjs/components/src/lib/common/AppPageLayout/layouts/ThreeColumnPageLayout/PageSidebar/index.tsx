import type {ReactNode} from 'react';

import {useTheme} from 'styled-components';
import AppDrawer from '../../../../../antd/AppDrawer';
import {
  StyledAddBtn,
  StyledAddBtnView,
  StyledLoadingContainer,
  StyledMainMenu,
  StyledScrollbar,
  StyledSidebar,
  StyledSkeletonButton,
} from './index.styled';
import {type MenuProps, Space} from 'antd';
import {MdArrowForwardIos, MdEdit} from 'react-icons/md';
import {RiVideoAddLine} from 'react-icons/ri';
import {useAppActionsContext, useAppContext, useAuthContext, useOrgContext,} from '@unpod/providers';
import {useMediaQuery} from 'react-responsive';
import {useParams, useRouter} from 'next/navigation';
import {DesktopWidthQuery} from '@unpod/constants';

type PageSidebarProps = Omit<MenuProps, 'items' | 'onClick'> & {
  loading?: boolean;
  items: MenuProps['items'];
  onMenuClick?: MenuProps['onClick'];
  children?: ReactNode;
  reloadDataApi?: () => void;
  hidePageHeader?: boolean;
  isAllowedAdd?: boolean;
};

const PageSidebar = ({
                       loading,
                       items,
                       onMenuClick,
                       children,
                       reloadDataApi,
                       hidePageHeader,
                       isAllowedAdd,
                       ...restProps
                     }: PageSidebarProps) => {
  const theme = useTheme();
  const isMobileView = useMediaQuery(DesktopWidthQuery);
  const router = useRouter();
  const {postSlug} = useParams<{ postSlug?: string }>();
  const {isAuthenticated, activeOrg} = useAuthContext();
  const {activeSpace} = useOrgContext();
  const {collapsed} = useAppContext();
  const {setCollapsed} = useAppActionsContext();

  // const isAllowedAdd = isAddAllowed(undefined, undefined, activeSpace);

  const onCreateClick = (postType: string) => {
    if (postSlug) {
      router.push(
        `/${activeOrg?.domain_handle}/${activeSpace?.slug}/${postSlug}/${postType}`,
      );
    } else if (activeSpace) {
      router.push(
        `/${activeOrg?.domain_handle}/${activeSpace?.slug}/${postType}`,
      );
    }
  };

  const sidebarContent = () => (
    <StyledScrollbar>
      {children}

      {loading ? (
        <StyledLoadingContainer>
          <StyledSkeletonButton active size="large" shape="round" block/>
          <StyledSkeletonButton active size="large" shape="round" block/>
          <StyledSkeletonButton active size="large" shape="round" block/>
          <StyledSkeletonButton active size="large" shape="round" block/>
          <StyledSkeletonButton active size="large" shape="round" block/>
        </StyledLoadingContainer>
      ) : (
        <StyledMainMenu
          mode="inline"
          items={items}
          onClick={onMenuClick}
          {...restProps}
        />
      )}

      {isAuthenticated && isAllowedAdd && (
        <StyledAddBtnView>
          <StyledAddBtn
            type="primary"
            onClick={() => onCreateClick('write')}
            disabled={!isAllowedAdd}
            block
            ghost
          >
            <Space align="center">
              <MdEdit fontSize={16}/>
              <span className="add-post-btn-text">Write</span>
            </Space>
            <MdArrowForwardIos fontSize={16}/>
          </StyledAddBtn>

          {/*{process.env.isDevMode === 'yes' && (
            <StyledAddBtn
              type="primary"
              onClick={() => onCreateClick('stream')}
              disabled={!isAllowedAdd}
              block
              ghost
            >
              <Space align="center">
                <MdStream fontSize={16} />
                <span className="add-post-btn-text">Stream</span>
              </Space>
              <MdArrowForwardIos fontSize={16} />
            </StyledAddBtn>
          )}*/}

          <StyledAddBtn
            type="primary"
            onClick={() => onCreateClick('upload')}
            disabled={!isAllowedAdd}
            block
            ghost
          >
            <Space align="center">
              <RiVideoAddLine fontSize={16}/>
              <span className="add-post-btn-text">Upload</span>
            </Space>
            <MdArrowForwardIos fontSize={16}/>
          </StyledAddBtn>
        </StyledAddBtnView>
      )}
    </StyledScrollbar>
  );

  return isMobileView ? (
    <AppDrawer
      placement="left"
      closable={false}
      width={theme?.layout.main.sidebar.width}
      onClose={() => setCollapsed(false)}
      open={collapsed}
      bodyStyle={{padding: 0}}
    >
      {sidebarContent()}
    </AppDrawer>
  ) : (
    <StyledSidebar
      collapsed={collapsed}
      width={theme?.layout.main.sidebar.width}
      collapsedWidth={0}
      trigger={null}
      collapsible
      $hidePageHeader={hidePageHeader}
    >
      {sidebarContent()}
    </StyledSidebar>
  );
};

export default PageSidebar;
