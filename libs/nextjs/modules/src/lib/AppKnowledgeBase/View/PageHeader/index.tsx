'use client';
import {Fragment, type ReactNode, useEffect, useState} from 'react';
import {getPostIcon, isShareBtnAccessAllowed,} from '@unpod/helpers/PermissionHelper';
import {Badge} from 'antd';
import {useAuthContext} from '@unpod/providers';
import PermissionPopover from '@unpod/components/common/PermissionPopover';
import type {PermissionMember} from '@unpod/components/common/PermissionPopover/types';
import {useMediaQuery} from 'react-responsive';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import AppSharedUsers from '@unpod/components/modules/AppSharedUsers';
import RequestPopover from '@unpod/components/common/RequestPopover';
import AppPageHeader, {AppHeaderButton,} from '@unpod/components/common/AppPageHeader';
import {TabWidthQuery} from '@unpod/constants';
import {useIntl} from 'react-intl';

type PageHeaderProps = {
  currentKb: any;
  setCurrentKb: (kb: any) => void;
  rightOptions?: ReactNode;
  pageTitle?: ReactNode;
  dropdownMenu?: ReactNode;
  documents?: any[];
  selectedRowKeys?: any[];
  setSelectedRowKeys?: (keys: any[]) => void;
};

const PageHeader = ({
                      currentKb,
                      setCurrentKb,
                      rightOptions,
                      pageTitle,
                      dropdownMenu,
                      documents,
                      selectedRowKeys,
                      setSelectedRowKeys,
                    }: PageHeaderProps) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const {isAuthenticated} = useAuthContext();
  const {formatMessage} = useIntl();
  const [openPermissionManager, setOpenPermissionManager] = useState(false);
  const [openRequestManager, setOpenRequestManager] = useState(false);
  const [userList, setUserList] = useState<PermissionMember[]>([]);

  useEffect(() => {
    if (currentKb?.users) {
      setUserList(
        currentKb?.users.map((item: PermissionMember) => ({
          ...item,
          email: item.email,
          role_code: item.role,
        })),
      );
    }
  }, [currentKb?.users]);

  const getBtnText = () => {
    if (
      currentKb?.final_role === ACCESS_ROLE.OWNER ||
      currentKb?.final_role === ACCESS_ROLE.EDITOR
    ) {
      return 'common.share';
    } else if (currentKb?.final_role === ACCESS_ROLE.VIEWER) {
      return 'common.viewOnly';
    }
    return 'common.join';
  };

  return (
    <AppPageHeader
      hideToggleBtn
      pageTitle={dropdownMenu || currentKb?.name || pageTitle}
      rightOptions={
        <Fragment>
          {currentKb && !isTabletOrMobile && (
            <Fragment>
              {/*{currentKb?.content_type === 'contact' && (*/}
              {/*  <AppSpaceContactCall*/}
              {/*    space={currentKb}*/}
              {/*    documents={documents}*/}
              {/*    selectedRowKeys={selectedRowKeys}*/}
              {/*    setSelectedRowKeys={setSelectedRowKeys}*/}
              {/*  />*/}
              {/*)}*/}

              <AppSharedUsers users={userList}/>

              {isAuthenticated &&
                (isShareBtnAccessAllowed(null, null, currentKb) ? (
                  <PermissionPopover
                    open={openPermissionManager}
                    onOpenChange={setOpenPermissionManager}
                    title={formatMessage({id: 'common.share'})}
                    placement="bottomRight"
                    currentData={currentKb}
                    setCurrentData={setCurrentKb}
                    userList={userList}
                    setUserList={setUserList}
                    linkShareable
                    type="space"
                  >
                    <Badge count={(currentKb?.access_request || []).length}>
                      <AppHeaderButton
                        type="primary"
                        shape="round"
                        icon={
                          <span
                            className="anticon"
                            style={{verticalAlign: 'middle'}}
                          >
                            {getPostIcon(currentKb?.privacy_type)}
                          </span>
                        }
                        onClick={() => setOpenPermissionManager(true)}
                      >
                        {formatMessage({id: getBtnText()})}
                      </AppHeaderButton>
                    </Badge>
                  </PermissionPopover>
                ) : (
                  <RequestPopover
                    open={openRequestManager}
                    onOpenChange={setOpenRequestManager}
                    currentData={currentKb}
                    setCurrentData={setCurrentKb}
                    type="space"
                    title={formatMessage({id: 'common.requestAccess'})}
                    placement="bottomRight"
                  >
                    <AppHeaderButton
                      type="primary"
                      shape="round"
                      icon={
                        <span
                          className="anticon"
                          style={{verticalAlign: 'middle'}}
                        >
                          {getPostIcon(currentKb?.privacy_type)}
                        </span>
                      }
                      onClick={() => setOpenRequestManager(true)}
                    >
                      {formatMessage({id: getBtnText()})}
                    </AppHeaderButton>
                  </RequestPopover>
                ))}
            </Fragment>
          )}

          {rightOptions}
        </Fragment>
      }
    />
  );
};

export default PageHeader;
