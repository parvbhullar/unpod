import PeopleOverview from './Overview';
import Conversations from './Conversation';

export const getTabItems = (
  activeTab: string,
  formatMessage: (msg: any) => string,
) => {
  return [
    {
      key: 'overview',
      label: formatMessage({ id: 'tab.overview' }),
      children: activeTab === 'overview' && <PeopleOverview />,
    },
    {
      key: 'conversation',
      label: formatMessage({ id: 'tab.conversation' }),
      children: activeTab === 'conversation' && <Conversations />,
    },
    /*{
      key: 'tasks',
      label: 'Tasks',
      children: <Tasks />,
    },*/
  ];
};
