import { FaList } from 'react-icons/fa';
import {
  MdCallMade,
  MdCallReceived,
  MdCheck,
  MdClose,
  MdPhone,
  MdPhoneMissed,
  MdSend,
  MdThumbDown,
  MdThumbUp,
} from 'react-icons/md';

export const CALL_STATUS_OPTIONS = [
  { name: 'call.all', slug: 'all', icon: <FaList size={14} /> },
  { name: 'call.completed', slug: 'completed', icon: <MdCheck size={16} /> },
  { name: 'call.failed', slug: 'failed', icon: <MdClose size={16} /> },
];

export const CALL_FILTER_STATUS_OPTIONS = [
  { name: 'call.completed', slug: 'Completed', icon: <MdCheck size={16} /> },
  { name: 'call.callBack', slug: 'Call Back', icon: <MdPhone size={16} /> },
  {
    name: 'call.sendDetails',
    slug: 'Send Details',
    icon: <MdSend size={16} />,
  },
  {
    name: 'call.interested',
    slug: 'Interested',
    icon: <MdThumbUp size={16} />,
  },
  { name: 'call.failed', slug: 'failed', icon: <MdClose size={16} /> },
  {
    name: 'call.notInterested',
    slug: 'Not Interested',
    icon: <MdThumbDown size={16} />,
  },
  {
    name: 'call.notConnected',
    slug: 'Not Connected',
    icon: <MdPhoneMissed size={16} />,
  },
];

export const CALL_TYPE_OPTIONS = [
  { name: 'call.all', slug: 'all', icon: <FaList size={14} /> },
  {
    name: 'call.inbound',
    slug: 'inbound',
    icon: <MdCallReceived size={16} />,
  },
  {
    name: 'call.outbound',
    slug: 'outbound',
    icon: <MdCallMade size={16} />,
  },
];
