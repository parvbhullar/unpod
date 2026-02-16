import { useState } from 'react';
import {
  StyledContainer,
  StyledRoot,
  StyledSegmentSticky,
} from './index.styled';
import { TasksTabs } from './TasksTabs';
import AllTasks from './AllTasks';
import CompletedTasks from './CompletedTasks';
import FailedTasks from './FailedTasks';
import UpcomingTasks from './UpcomingTasks';
import AppSegmented from '@unpod/components/antd/AppSegmented';

const Tasks = () => {
  const [activeTab, setActiveTab] = useState('all');
  return (
    <StyledRoot>
      <StyledSegmentSticky>
        <AppSegmented
          value={activeTab}
          onChange={(val) => setActiveTab(String(val))}
          tabs={TasksTabs as any}
        />
      </StyledSegmentSticky>
      <StyledContainer>
        {activeTab === 'all' && <AllTasks />}
        {activeTab === 'upcoming' && <UpcomingTasks />}
        {activeTab === 'completed' && <CompletedTasks />}
        {activeTab === 'failed' && <FailedTasks />}
      </StyledContainer>
    </StyledRoot>
  );
};

export default Tasks;
