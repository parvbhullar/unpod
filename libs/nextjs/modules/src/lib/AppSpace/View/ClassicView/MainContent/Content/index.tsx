import { useAppSpaceContext } from '@unpod/providers';
import { StyledTabContent } from './index.styled';
import { clsx } from 'clsx';
import Documents from './Documents';
import { SpaceSkeleton } from '@unpod/skeleton';
import Tasks from './Tasks';
import Dashboard from './Dashboard';
import Conversation from './Conversation';
import CallLogs from './Calls';

const Content = ({
  onTabChange,
  threadType,
  setThreadType,
  tasksRef,
  dashboardRef,
}: {
  onTabChange: (tab: string) => void;
  threadType: any;
  setThreadType: (val: any) => void;
  tasksRef: any;
  dashboardRef: any;
}) => {
  const { activeTab, currentSpace, notesRef } = useAppSpaceContext();
  const ConversationAny = Conversation as any;
  const DashboardAny = Dashboard as any;
  const TasksAny = Tasks as any;

  return (
    <>
      <StyledTabContent
        className={clsx({
          active: activeTab === 'call',
        })}
      >
        {activeTab === 'call' && <CallLogs />}
      </StyledTabContent>

      <StyledTabContent
        className={clsx({
          active: activeTab === 'doc',
        })}
      >
        {activeTab === 'doc' && <Documents />}
      </StyledTabContent>

      {activeTab ? (
        <StyledTabContent
          className={clsx({
            active: activeTab === 'chat',
          })}
        >
          {activeTab === 'chat' && (
            <ConversationAny
              onNoteSaved={() => {
                notesRef?.current?.refreshData?.();
                onTabChange('note');
              }}
            />
          )}
        </StyledTabContent>
      ) : (
        <SpaceSkeleton />
      )}
      {/*

      <StyledTabContent
        className={clsx({
          active: activeTab === 'note',
        })}
      >
        {activeTab === 'note' && (
          <NotesAny threadType={threadType} setThreadType={setThreadType} />
        )}
      </StyledTabContent>
*/}

      <StyledTabContent
        className={clsx({
          active: activeTab === 'analytics',
        })}
      >
        {activeTab === 'analytics' && (
          <DashboardAny currentSpace={currentSpace} ref={dashboardRef} />
        )}
      </StyledTabContent>

      <StyledTabContent
        className={clsx({
          active: activeTab === 'logs',
        })}
      >
        {activeTab === 'logs' && (
          <TasksAny currentSpace={currentSpace} ref={tasksRef} />
        )}
      </StyledTabContent>
    </>
  );
};

export default Content;
