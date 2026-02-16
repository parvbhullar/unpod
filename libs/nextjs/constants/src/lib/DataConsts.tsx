import { ReactNode } from 'react';
import {
  MdChecklist,
  MdDataObject,
  MdFormatListBulleted,
  MdLink,
  MdLockOutline,
  MdPhone,
  MdPublic,
} from 'react-icons/md';
import { RiUserSharedLine } from 'react-icons/ri';
import {
  AlignLeftOutlined,
  CalculatorOutlined,
  CalendarOutlined,
  FileAddOutlined,
  MailOutlined,
  ProfileOutlined,
} from '@ant-design/icons';
import { BsTextareaResize } from 'react-icons/bs';

export const TAG_BACKGROUND_COLORS = ['#FCFFD5', '#CEFCFF', '#CED3FF'] as const;

export type PrivacyType = {
  key: string;
  value: string;
  label: string;
  icon: ReactNode;
};

export const PRIVACY_TYPES: PrivacyType[] = [
  {
    key: 'public',
    value: 'public',
    label: 'permission.public',
    icon: (
      <span className="anticon">
        <MdPublic fontSize={21} />
      </span>
    ),
  },
  {
    key: 'shared',
    value: 'shared',
    label: 'permission.private',
    icon: (
      <span className="anticon">
        <RiUserSharedLine fontSize={21} />
      </span>
    ),
  },
];

export type PermissionType = {
  key: string;
  label: string;
  icon: ReactNode;
  iconOnly: ReactNode;
};

export const PERMISSION_TYPES: PermissionType[] = [
  {
    key: 'public',
    label: 'permission.public',
    icon: (
      <span className="anticon">
        <MdPublic fontSize={18} />
      </span>
    ),
    iconOnly: <MdPublic fontSize={18} />,
  },
  {
    key: 'shared',
    label: 'permission.shared',
    icon: (
      <span className="anticon">
        <RiUserSharedLine fontSize={18} />
      </span>
    ),
    iconOnly: <RiUserSharedLine fontSize={18} />,
  },
  {
    key: 'private',
    label: 'permission.private',
    icon: (
      <span className="anticon">
        <MdLockOutline fontSize={18} />
      </span>
    ),
    iconOnly: <MdLockOutline fontSize={18} />,
  },
];

export type ContentItem = {
  label?: string;
  key: string;
  type?: string;
};

export const CRETE_CONTENT_ITEMS: ContentItem[] = [
  {
    label: 'Upload Video/Audio',
    key: 'upload-podcast',
  },
  {
    type: 'divider',
    key: 'divider',
  },
  {
    label: 'Write a Post',
    key: 'create-note',
  },
];

export const INPUT_TYPE_ICONS: Record<string, ReactNode> = {
  text: <AlignLeftOutlined />,
  string: <AlignLeftOutlined />,
  textarea: <BsTextareaResize />,
  email: <MailOutlined />,
  number: <CalculatorOutlined />,
  integer: <CalculatorOutlined />,
  file: <FileAddOutlined />,
  phone: <MdPhone />,
  url: <MdLink />,
  json: <MdDataObject fontSize={20} style={{ marginLeft: -3 }} />,
  form: <MdFormatListBulleted fontSize={20} style={{ marginLeft: -3 }} />,
  date: <CalendarOutlined />,
  time: <CalendarOutlined />,
  datetime: <CalendarOutlined />,
  checkboxes: <MdChecklist />,
  select: <ProfileOutlined />,
  'multi-select': <ProfileOutlined />,
};

export type InputTypeConfig = {
  type: string;
  placeholder?: string;
  required?: boolean;
  mode?: string;
};

export const INPUT_TYPES: InputTypeConfig[] = [
  {
    type: 'text',
    placeholder: 'input.text',
    required: true,
  },
  {
    type: 'textarea',
    placeholder: 'input.textarea',
    required: true,
  },
  {
    type: 'file',
    placeholder: 'input.file',
    required: true,
  },
  { type: 'separator' },

  {
    type: 'json',
    placeholder: 'input.json',
    required: true,
  },
  {
    type: 'form',
    placeholder: 'input.form',
    required: true,
  },
  {
    type: 'number',
    placeholder: 'input.number',
    required: true,
  },
  { type: 'separator' },

  {
    type: 'email',
    placeholder: 'input.email',
    required: true,
  },
  {
    type: 'phone',
    placeholder: 'input.phone',
    required: true,
  },
  {
    type: 'url',
    placeholder: 'input.url',
    required: true,
  },
  { type: 'separator' },

  {
    type: 'date',
    placeholder: 'input.date',
    required: true,
  },
  {
    type: 'time',
    placeholder: 'input.time',
    required: true,
  },
  {
    type: 'datetime',
    placeholder: 'input.datetime',
    required: true,
  },
  { type: 'separator' },

  {
    type: 'checkboxes',
    placeholder: 'input.checklist',
    required: true,
  },
  {
    type: 'select',
    placeholder: 'input.singleSelect',
    required: true,
  },
  {
    type: 'multi-select',
    mode: 'multiple',
    placeholder: 'input.multiSelect',
    required: true,
  },
];

export const INPUT_DEFAULT_VALUES: Record<string, boolean | null | string> = {
  true: true,
  false: false,
  null: null,
  empty_string: '',
};

export type DefaultValueType =
  | string
  | number
  | boolean
  | null
  | Record<string, unknown>
  | unknown[];

export const TYPE_BASED_DEFAULT_VALUES: Record<string, DefaultValueType> = {
  text: '',
  string: '',
  textarea: '',
  email: '',
  number: 0,
  integer: 0,
  file: null,
  phone: '',
  url: '',
  json: {},
  date: null,
  time: null,
  datetime: null,
  select: null,
  multi_select: [],
};
