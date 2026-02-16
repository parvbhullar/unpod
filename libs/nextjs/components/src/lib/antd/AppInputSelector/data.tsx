import {
  AlignLeftOutlined,
  CalculatorOutlined,
  CalendarOutlined,
  FileAddOutlined,
  MailOutlined,
  ProfileOutlined,
} from '@ant-design/icons';

import { MdChecklist, MdDataObject, MdLink, MdPhone } from 'react-icons/md';
import { BsTextareaResize } from 'react-icons/bs';

export const inputTypeIcons = {
  text: <AlignLeftOutlined />,
  textarea: <BsTextareaResize />,
  email: <MailOutlined />,
  number: <CalculatorOutlined />,
  file: <FileAddOutlined />,
  phone: <MdPhone />,
  url: <MdLink />,
  json: <MdDataObject fontSize={20} style={{ marginLeft: -3 }} />,
  date: <CalendarOutlined />,
  time: <CalendarOutlined />,
  'date-time': <CalendarOutlined />,
  checkboxes: <MdChecklist />,
  select: <ProfileOutlined />,
  'multi-select': <ProfileOutlined />,
};

export const inputTypes = [
  {
    type: 'text',
    placeholder: 'Text',
    required: true,
  },
  {
    type: 'textarea',
    placeholder: 'Text area',
    required: true,
  },
  {
    type: 'file',
    placeholder: 'File',
    required: true,
  },
  {
    type: 'separator',
  },
  {
    type: 'json',
    placeholder: 'JSON',
    required: true,
  },
  {
    type: 'number',
    placeholder: 'Number',
    required: true,
  },
  {
    type: 'separator',
  },
  {
    type: 'email',
    placeholder: 'Email address',
    required: true,
  },
  {
    type: 'phone',
    placeholder: 'Phone number',
    required: true,
  },
  {
    type: 'url',
    placeholder: 'URL',
    required: true,
  },
  {
    type: 'separator',
  },
  {
    type: 'date',
    placeholder: 'Date',
    required: true,
  },
  {
    type: 'time',
    placeholder: 'Time',
    required: true,
  },
  {
    type: 'date-time',
    placeholder: 'Date and Time',
    required: true,
  },
  {
    type: 'separator',
  },
  {
    type: 'checkboxes',
    placeholder: 'Check List',
    required: true,
  },
  {
    type: 'select',
    placeholder: 'Single select',
    required: true,
  },
  {
    type: 'multi-select',
    mode: 'multiple',
    placeholder: 'Multi select',
    required: true,
  },
];
