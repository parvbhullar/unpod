import { ReactNode } from 'react';
import {
  MdOutlineEmail,
  MdOutlineExtension,
  MdOutlineWorkspaces,
  MdPlayCircleOutline,
} from 'react-icons/md';
import { RiContactsLine, RiImage2Line, RiTableView } from 'react-icons/ri';
import { GrDocumentText } from 'react-icons/gr';
import { SiGmail } from 'react-icons/si';

export type ContentTypeItem = {
  id: string;
  name: string;
  icon?: ReactNode;};

export const contentTypeData: ContentTypeItem[] = [
  {
    id: 'document',
    name: 'space.document',
    icon: <GrDocumentText fontSize={16} />,
  },
  {
    id: 'table',
    name: 'space.table',
    icon: <RiTableView fontSize={16} />,
  },
  {
    id: 'email',
    name: 'space.email',
    icon: <MdOutlineEmail fontSize={16} />,
  },
  {
    id: 'contact',
    name: 'space.contact',
    icon: <RiContactsLine fontSize={16} />,
  },
];

export const spaceContentTypeData: ContentTypeItem[] = [
  {
    id: 'contact',
    name: 'space.contact',
    icon: <RiContactsLine fontSize={16} />,
  },
];

export const COLLECTION_TYPE_DATA: ContentTypeItem[] = [
  ...spaceContentTypeData,
];

const PLAIN_TEXT_FILE_EXTENSIONS =
  '.txt,.md,.mdx,.conf,.log,.json,.xml,.yml,.yaml';

const TABULAR_FILE_EXTENSIONS = '.csv, .tsv, .record, .xlsx';
const DOCUMENT_FILE_EXTENSIONS = '.pdf,.docx,.pptx,.xlsx,.eml,.epub,.html';

export const allowedFileTypes: Record<string, string> = {
  document: `${PLAIN_TEXT_FILE_EXTENSIONS},${TABULAR_FILE_EXTENSIONS},${DOCUMENT_FILE_EXTENSIONS}`,
  table: TABULAR_FILE_EXTENSIONS,
  image: '.jpg, .jpeg, .png, .gif, .svg, .bmp, .tiff, .webp, .ico, .psd, .ai',
  media:
    '.mp3, .mp4, .avi, .mov, .wmv, .flv, .mkv, .webm, .aac, .wav, .ogg, .flac',
  contact: TABULAR_FILE_EXTENSIONS,
};

export type SpaceContentType = {
  id: string;
  name: string;};

export const SPACE_CONTENT_TYPES: SpaceContentType[] = [
  {
    id: 'general',
    name: 'space.general',
  },
  {
    id: 'email',
    name: 'space.email',
  },
  {
    id: 'contact',
    name: 'space.contact',
  },
];

export const REQUIRED_CONTACT_FIELDS = ['name', 'contact_number'] as const;

export type RequiredContactField = (typeof REQUIRED_CONTACT_FIELDS)[number];

export type ContactSpaceField = {
  id: number;
  name: string;
  type: string;
  placeholder: string;
  title: string;
  description: string;
  defaultValue: string;
  required?: boolean;};

export const CONTACT_SPACE_FIELDS: ContactSpaceField[] = [
  {
    id: 101,
    name: 'name',
    type: 'text',
    placeholder: 'Name',
    title: 'Name',
    description: 'Contact Name',
    defaultValue: '',
    required: true,
  },
  {
    id: 102,
    name: 'email',
    type: 'email',
    placeholder: 'Email',
    title: 'Email',
    description: '',
    defaultValue: '',
    required: false,
  },
  {
    id: 103,
    name: 'contact_number',
    type: 'phone',
    placeholder: 'Contact Number',
    title: 'Contact Number',
    description: '',
    defaultValue: '',
    required: true,
  },
  {
    id: 104,
    name: 'occupation',
    type: 'text',
    placeholder: 'Occupation',
    title: 'Occupation',
    description: '',
    defaultValue: '',
  },
];

export const CONTENT_TYPE_ICONS: Record<string, ReactNode> = {
  general: <MdOutlineWorkspaces fontSize={16} />,
  email: <MdOutlineEmail fontSize={16} />,
  contact: <RiContactsLine fontSize={16} />,
  document: <GrDocumentText fontSize={16} />,
  table: <RiTableView fontSize={16} />,
  image: <RiImage2Line fontSize={16} />,
  media: <MdPlayCircleOutline fontSize={16} />,
};

export const CONNECTOR_ICONS: Record<string, ReactNode> = {
  default: <MdOutlineExtension fontSize={16} />,
  gmail: <SiGmail fontSize={16} />,
};

export const SPACE_VISIBLE_CONTENT_TYPES = ['contact'] as const;

export type SpaceVisibleContentType =
  (typeof SPACE_VISIBLE_CONTENT_TYPES)[number];
