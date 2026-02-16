import { FaList } from 'react-icons/fa';
import { MdCheck, MdClose } from 'react-icons/md';

export const STATUS_OPTIONS = [
  { name: 'All', slug: 'all', icon: <FaList size={14} /> },
  {
    name: 'Completed',
    slug: 'completed',
    icon: <MdCheck size={16} />,
  },
  { name: 'Failed', slug: 'failed', icon: <MdClose size={16} /> },
];
