import type { ComponentType } from 'react';
import { useRef, useState } from 'react';
import { Tooltip } from 'antd';
import { MdRefresh } from 'react-icons/md';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import AppSpaceContactCall from '@unpod/components/modules/AppSpaceContactCall';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import Header from './Header';
import Content from './Content';
import AddNewTask from './Content/Tasks/AddNew';
import { SpaceSkeleton } from '@unpod/skeleton';
import { useIntl } from 'react-intl';
import People from '../Sidebar/People';

const MainContent = () => {
  const {
    setSelectedDocs,
    setActiveDocument,
    setActiveConversation,
    setActiveNote,
    setDocumentMode,
  } = useAppSpaceActionsContext();
  const { activeTab, currentSpace } = useAppSpaceContext();
  const { formatMessage } = useIntl();
  const [threadType, setThreadType] = useState('');

  const tasksRef = useRef<{ refreshData?: () => void } | null>(null);
  const dashboardRef = useRef<{ refreshData?: () => void } | null>(null);

  const onTabChange = (key: string) => {
    if (key !== 'back' && key !== 'close') {
      // setActiveTab(key);
      if (key !== 'tasks') {
        setSelectedDocs([]);
      }
    } else if (key === 'back') {
      if (activeTab === 'doc' || activeTab === 'call') {
        setActiveDocument(null);
        setDocumentMode('view');
      } else if (activeTab === 'chat') {
        setActiveConversation(null);
      } else if (activeTab === 'note') {
        setActiveNote(null);
        setThreadType('');
      }
    }
  };

  const onAddClick = (key: string) => {
    if (key === 'document') {
      setDocumentMode('add');
      setActiveDocument(null);
    } else {
      setThreadType(key);
      setActiveNote(null);
    }
  };

  const HeaderAny = Header as ComponentType<any>;

  return currentSpace ? (
    <>
      <HeaderAny
        activeTab={activeTab}
        onChange={onTabChange}
        onAddClick={onAddClick}
        taskCallButton={
          activeTab === 'logs' ? (
            currentSpace.content_type === 'contact' ? (
              <AppSpaceContactCall
                idKey="document_id"
                onFinishSchedule={() => {
                  tasksRef.current?.refreshData?.();
                }}
                onRefreshTasks={tasksRef.current?.refreshData}
                drawerChildren={<People />}
              />
            ) : (
              <AddNewTask
                idKey="document_id"
                onFinishSchedule={() => {
                  tasksRef.current?.refreshData?.();
                }}
              />
            )
          ) : (
            activeTab === 'analytics' && (
              <Tooltip title={formatMessage({ id: 'common.refresh' })}>
                <AppHeaderButton
                  type="default"
                  shape="circle"
                  size="small"
                  icon={<MdRefresh fontSize={24} />}
                  onClick={() => {
                    dashboardRef.current?.refreshData?.();
                  }}
                />
              </Tooltip>
            )
          )
        }
      />

      <Content
        threadType={threadType}
        setThreadType={setThreadType}
        onTabChange={onTabChange}
        tasksRef={tasksRef}
        dashboardRef={dashboardRef}
      />
    </>
  ) : (
    <SpaceSkeleton />
  );
};

export default MainContent;
