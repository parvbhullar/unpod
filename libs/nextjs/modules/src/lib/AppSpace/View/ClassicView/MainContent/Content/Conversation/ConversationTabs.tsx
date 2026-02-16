import { MdDashboard } from 'react-icons/md';
import { IoDocumentText } from 'react-icons/io5';
import { FaClipboardCheck } from 'react-icons/fa';

export const ConversationTabs = [
  {
    value: 'overview',
    label: 'conversation.overview',
    icon: <MdDashboard size={16} />,
  },
  {
    value: 'conversation',
    label: 'conversation.conversation',
    icon: <IoDocumentText size={16} />,
  },
  {
    value: 'tasks',
    label: 'conversation.tasks',
    icon: <FaClipboardCheck size={16} />,
  },
  // {
  //   value: 'data',
  //   labelKey: 'conversation.data',
  //   icon: <MdCheckCircle size={16} fontSize={16} />,
  // },
];
