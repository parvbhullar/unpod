import type {ComponentType} from 'react';
import {useState} from 'react';
import {getPostIcon, isShareBtnAccessAllowed,} from '@unpod/helpers/PermissionHelper';
import {Badge, Space} from 'antd';
import {AppHeaderButton} from '@unpod/components/common/AppPageHeader';
import {useAppSpaceActionsContext, useAppSpaceContext, useAuthContext,} from '@unpod/providers';
import PermissionPopover from '@unpod/components/common/PermissionPopover';
import {useMediaQuery} from 'react-responsive';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import RequestPopover from '@unpod/components/common/RequestPopover';
import SubscribeModal from './SubscribeModal';
import {TabWidthQuery} from '@unpod/constants';
import AppSharedUsers from '@unpod/components/modules/AppSharedUsers';
import {useIntl} from 'react-intl';
import type {Conversation, Document, Spaces} from '@unpod/constants/types';

type SharedData = {
  final_role?: string;
  users?: unknown[];
  access_request?: unknown[];
  privacy_type?: string;
  token?: string;
  [key: string]: unknown;
};

const PermissionPopoverAny = PermissionPopover as ComponentType<any>;
const RequestPopoverAny = RequestPopover as ComponentType<any>;

const getCurrentObjectData = (
  currentSpace: SharedData | null,
  activeConversation: SharedData | null,
  activeNote: SharedData | null,
  activeDocument: SharedData | null,
  activeTab: string,
) => {
  if (activeTab === 'chat' && activeConversation) {
    return {type: 'chat', data: activeConversation};
  } else if (activeTab === 'note' && activeNote) {
    return {type: 'note', data: activeNote};
  } else if (activeTab === 'doc' && activeDocument) {
    return {type: 'doc', data: activeDocument};
  }
  return {type: 'space', data: currentSpace};
};

const getBtnText = (currentData: SharedData | null) => {
  if (
    currentData?.final_role === ACCESS_ROLE.OWNER ||
    currentData?.final_role === ACCESS_ROLE.EDITOR
  ) {
    return 'common.share';
  } else if (currentData?.final_role === ACCESS_ROLE.VIEWER) {
    return 'common.viewOnly';
  }

  return 'common.subscribe';
};

const SpaceOptions = () => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const {
    setCurrentSpace,
    setActiveConversation,
    setActiveNote,
    setActiveDocument,
  } = useAppSpaceActionsContext();
  const {
    currentSpace,
    activeConversation,
    activeTab,
    activeNote,
    activeDocument,
  } = useAppSpaceContext();
  const [openPermissionManager, setOpenPermissionManager] = useState(false);
  const [openRequestManager, setOpenRequestManager] = useState(false);
  const {isAuthenticated} = useAuthContext();
  const {formatMessage} = useIntl();

  const {type, data: currentData} = getCurrentObjectData(
    currentSpace as SharedData | null,
    activeConversation as SharedData | null,
    activeNote as SharedData | null,
    activeDocument as SharedData | null,
    activeTab,
  );
  const privacyType = currentData?.privacy_type || 'public';

  const setCurrentData = (data: SharedData | null) => {
    switch (type) {
      case 'space':
        setCurrentSpace(data as Spaces | null);
        break;
      case 'chat':
        setActiveConversation(data as Conversation | null);
        break;
      case 'note':
        setActiveNote(data as Conversation | null);
        break;
      case 'doc':
        setActiveDocument(data as Document | null);
        break;
      default:
        break;
    }
  };

  return (
    <Space align="center">
      <AppSharedUsers users={currentData?.users as any}/>

      {isAuthenticated &&
        !isTabletOrMobile &&
        (isShareBtnAccessAllowed(null, null, currentData as any) ? (
          <PermissionPopoverAny
            open={openPermissionManager}
            onOpenChange={setOpenPermissionManager}
            currentData={currentData}
            setCurrentData={setCurrentData}
            linkShareable
            type={type}
          >
            <Badge count={(currentData?.access_request || []).length}>
              <AppHeaderButton
                type="primary"
                shape="round"
                size="small"
                icon={
                  <span
                    className={`anticon ${privacyType}-icon`}
                    style={{verticalAlign: 'middle'}}
                  >
                    {getPostIcon(privacyType)}
                  </span>
                }
                onClick={() => setOpenPermissionManager(true)}
              >
                {formatMessage({id: getBtnText(currentData)})}
              </AppHeaderButton>
            </Badge>
          </PermissionPopoverAny>
        ) : (
          <RequestPopoverAny
            type={type}
            open={openRequestManager}
            onOpenChange={setOpenRequestManager}
            currentData={currentData}
            setCurrentData={setCurrentData}
            title={formatMessage({id: 'common.requestAccess'})}
          >
            <AppHeaderButton
              type="primary"
              shape="round"
              size="small"
              icon={
                <span
                  className={`anticon ${privacyType}-icon`}
                  style={{verticalAlign: 'middle'}}
                >
                  {getPostIcon(privacyType)}
                </span>
              }
              onClick={() => setOpenRequestManager(true)}
            >
              {formatMessage({id: getBtnText(currentData)})}
            </AppHeaderButton>
          </RequestPopoverAny>
        ))}

      {!isAuthenticated &&
        currentData?.token &&
        currentData?.privacy_type === 'public' && (
          <SubscribeModal currentData={currentData as any} type={type}/>
        )}
    </Space>
  );
};

export default SpaceOptions;
