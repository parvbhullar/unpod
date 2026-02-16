import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import {
  StyledHeaderActions,
  StyledHeaderIcon,
  StyledHeaderTitle,
  StyledMainHeaderContent,
} from './index.styled';
import UserAvatar from '@unpod/components/common/UserAvatar';
import { getFirstLetter } from '@unpod/helpers/StringHelper';
import DocumentHeaderDetails from './DocumentHeaderDetails';
import AppSpaceHeaderMenus from '@unpod/components/common/AppSpaceHeaderMenus';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import SpaceOptions from './components/SpaceOptions';
import AppSpaceContactCall from '@unpod/components/modules/AppSpaceContactCall';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import { isEditAccessAllowed } from '@unpod/helpers/PermissionHelper';
import { Dropdown, Flex, Typography } from 'antd';
import { useRouter } from 'next/navigation';
import { MdAdd, MdEdit } from 'react-icons/md';
import { RiVideoAddLine } from 'react-icons/ri';
import { getTimeFromNow } from '@unpod/helpers/DateHelper';
import People from '../../Sidebar/People';

const dropDownMenu = [
  {
    key: 'write',
    label: 'Write',
    icon: (
      <span className="ant-icon">
        <MdEdit size={20} />
      </span>
    ),
  },
  {
    key: 'upload',
    label: 'Upload',
    icon: (
      <span className="ant-icon">
        <RiVideoAddLine size={20} />
      </span>
    ),
  },
];

type HeaderInfo = {
  icon?: string;
  iconTooltip?: string;
  title?: string;
  subtitle?: string;
  email?: string;
  isUser?: boolean;
};

const getHeaderInfo = (type: string, currentData: any): HeaderInfo => {
  // console.log('currentData in header info', { currentData, type });
  switch (type) {
    case 'space': {
      return {
        icon: currentData?.name || 'SP',
        iconTooltip: currentData?.name || 'Space',
        title: currentData?.name || 'Space',
        subtitle: `Manage your conversations, documents, and tasks`,
      };
    }
    case 'note': {
      const userName = currentData.user;
      const noteTitle = currentData.title || currentData.context || 'Note';
      return {
        icon: userName,
        iconTooltip: userName,
        isUser: true,
        title: noteTitle,
        subtitle: `Note created ${
          currentData.created ? getTimeFromNow(currentData.created) : 'recently'
        }`,
      };
    }
    case 'doc': {
      return {
        icon: currentData.name || 'DO',
        iconTooltip: currentData.name || '',
        title: currentData.name || 'Document',
        subtitle: currentData.contact_number,
        email: currentData.email || `${currentData.name}@india.com`,
      };
    }
    case 'chat': {
      const userName = currentData.user;
      const threadTitle =
        currentData.context || currentData.title || 'Conversation';
      return {
        icon: userName,
        isUser: true,
        iconTooltip: userName,
        title: threadTitle,
        subtitle: `Conversation started ${
          currentData.created ? getTimeFromNow(currentData.created) : 'recently'
        }`,
      };
    }
    case 'call': {
      const customerName = currentData?.input?.name?.startsWith('sip')
        ? ''
        : currentData?.input?.name;
      const phoneNumber =
        currentData?.status === 'in_progress'
          ? currentData?.input?.contact_number
          : currentData?.output?.customer || currentData?.input?.contact_number;

      const subtitle = currentData.created
        ? getTimeFromNow(currentData.created)
        : '';

      return {
        icon: customerName || phoneNumber || 'Unknown',
        iconTooltip: customerName || phoneNumber || 'Unknown Caller',
        title: customerName || phoneNumber || 'Unknown Caller',
        subtitle,
      };
    }
    default: {
      return {
        icon: currentData.title || 'DO',
        iconTooltip: currentData.title || 'Document',
        title: currentData.title || 'Document',
        subtitle: `Last updated ${
          currentData.created ? getTimeFromNow(currentData.created) : 'recently'
        }`,
      };
    }
  }
};

const getCurrentObjectData = (
  currentSpace: any,
  activeConversation: any,
  activeNote: any,
  activeDocument: any,
  activeCall: any,
  activeTab: string,
) => {
  if (activeTab === 'chat' && activeConversation) {
    return { type: 'chat', data: activeConversation };
  } else if (activeTab === 'note' && activeNote) {
    return { type: 'note', data: activeNote };
  } else if (activeTab === 'doc' && activeDocument) {
    return { type: 'doc', data: activeDocument };
  } else if (activeTab === 'call' && activeCall) {
    return { type: 'call', data: activeCall };
  }
  return { type: 'space', data: currentSpace };
};
const { Text } = Typography;

type EntityHeaderProps = {
  onAddClick: (key: string) => void;
  taskCallButton?: ReactNode;
};

const EntityHeader = ({ onAddClick, taskCallButton }: EntityHeaderProps) => {
  const [addNew, setAddNew] = useState(false);
  const {
    activeDocument,
    currentSpace,
    activeNote,
    activeConversation,
    activeCall,
    activeTab,
  } = useAppSpaceContext();
  const { setActiveTab } = useAppSpaceActionsContext();
  const router = useRouter();
  const { type, data: currentData } = getCurrentObjectData(
    currentSpace,
    activeConversation,
    activeNote,
    activeDocument,
    activeCall,
    activeTab,
  );

  const onMenuClick = (option: { key: string }) => {
    if (option.key === 'write' || option.key === 'upload') {
      onAddClick(option.key);
    } else {
      router.push(`/thread/${option.key}/`);
    }
  };
  const headerInfo = getHeaderInfo(type, currentData);
  const isEditAllowed = useMemo(() => {
    return isEditAccessAllowed(null, null, currentSpace);
  }, [currentSpace]);

  const { icon, title, subtitle, email, isUser } = headerInfo;
  const isDocumentType = type === 'doc';
  const isCallType = type === 'call';
  const iconText = icon || '';

  return (
    <>
      <StyledMainHeaderContent>
        {activeTab !== 'logs' && activeTab !== 'analytics' ? (
          <Flex gap={10} align="center">
            {isUser ? (
              <UserAvatar
                user={{ full_name: iconText }}
                shape="square"
                size={32}
                fontSize={14}
              />
            ) : (
              <StyledHeaderIcon shape="square" size={32} data-icon={iconText}>
                {getFirstLetter(iconText)}
              </StyledHeaderIcon>
            )}
            <Flex vertical={true}>
              <StyledHeaderTitle level={2}>{title}</StyledHeaderTitle>
              {isDocumentType && (
                <DocumentHeaderDetails subtitle={subtitle} email={email} />
              )}
              {isCallType && subtitle && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {subtitle}
                </Text>
              )}
            </Flex>
          </Flex>
        ) : (
          <AppSpaceHeaderMenus
            addNew={addNew}
            setAddNew={setAddNew}
            isContentHeader={false}
            // breadcrumb={breadcrumb}
          />
        )}
      </StyledMainHeaderContent>

      <StyledHeaderActions>
        {isEditAllowed && (
          <>
            {activeTab === 'overview' && (
              <AppHeaderButton
                type="primary"
                shape="circle"
                size="small"
                icon={<MdAdd size={24} />}
                onClick={() => onAddClick('document')}
              />
            )}

            {activeTab === 'notes' && (
              <Dropdown menu={{ items: dropDownMenu, onClick: onMenuClick }}>
                <AppHeaderButton
                  type="primary"
                  shape="circle"
                  size="small"
                  icon={<MdAdd size={24} />}
                />
              </Dropdown>
            )}

            {activeTab !== 'doc' &&
              activeTab !== 'note' &&
              activeTab !== 'call' && <SpaceOptions />}

            {activeTab === 'note' && activeNote && (
              <AppHeaderButton
                type="primary"
                shape="circle"
                size="small"
                icon={<MdAdd size={24} />}
                onClick={() => onAddClick('note')}
              />
            )}

            {activeTab === 'call' && <SpaceOptions />}

            {activeTab === 'doc' &&
              currentSpace?.content_type === 'contact' && (
                <AppSpaceContactCall
                  idKey="document_id"
                  onFinishSchedule={() => {
                    setActiveTab('call');
                  }}
                  data={currentData}
                  hideExport
                  type="doc"
                  drawerChildren={<People />}
                />
              )}

            {taskCallButton}
          </>
        )}
      </StyledHeaderActions>
    </>
  );
};

export default EntityHeader;
