import type { Dispatch, SetStateAction } from 'react';
import type { PopoverProps } from 'antd';

import type {
  Organization,
  Spaces,
  Thread,
  User,
} from '@unpod/constants/types';

export type PermissionPopoverType =
  | 'org'
  | 'space'
  | 'note'
  | 'chat'
  | 'thread'
  | 'doc'
  | 'post';

export type PermissionMember = User & {
  email?: string;
  user_email?: string;
  role?: string;
  role_code?: string;
  joined?: boolean;
  invite_token?: string;
  request_token?: string;
  is_member?: boolean;
};

export type PermissionEntity = (Organization & Spaces & Thread) & {
  privacy_type?: string;
  final_role?: string;
  users?: PermissionMember[];
  access_request?: PermissionMember[] | number;
  allowed_operations?: string[];
};

export type RoleRecord = {
  role_code?: string;
  role_name?: string;
  [key: string]: unknown;
};

export type GlobalRoleMap = {
  space?: RoleRecord[];
  post?: RoleRecord[];
  [key: string]: unknown;
};

export type PermissionPopoverProps = Omit<
  PopoverProps,
  'title' | 'content' | 'placement'
> & {
  type?: PermissionPopoverType;
  title?: string;
  placement?: PopoverProps['placement'];
  linkShareable?: boolean;
  currentData?: PermissionEntity | null;
  setCurrentData: (data: PermissionEntity) => void;
  userList?: PermissionMember[];
  setUserList?: Dispatch<SetStateAction<PermissionMember[]>>;
};

export type InvitedUsersListProps = {
  type: PermissionPopoverType;
  currentData?: PermissionEntity | null;
  userList: PermissionMember[];
  onRemoveInvitedMember: (email: string) => void;
  onUpdateInvitedMember: (member: PermissionMember) => void;
};

export type InviteUserSectionProps = {
  type: PermissionPopoverType;
  userList: PermissionMember[];
  setUserList: Dispatch<SetStateAction<PermissionMember[]>>;
  currentData?: PermissionEntity | null;
  setCurrentData: (data: PermissionEntity) => void;
};

export type MemberRowProps = {
  type: PermissionPopoverType;
  member: PermissionMember;
  currentData?: PermissionEntity | null;
  onRemoveInvitedMember: (email: string) => void;
  onUpdateInvitedMember: (member: PermissionMember) => void;
};

export type RequestAccessRowProps = {
  type: PermissionPopoverType;
  currentData?: PermissionEntity | null;
  member: PermissionMember;
  onAcceptMemberRequest: (member: PermissionMember) => void;
  onDenyMemberRequest: (email: string) => void;
};

export type RequestedUsersListProps = {
  type: PermissionPopoverType;
  currentData?: PermissionEntity | null;
  userList: PermissionMember[];
  setUserList: Dispatch<SetStateAction<PermissionMember[]>>;
  setCurrentData: (data: PermissionEntity) => void;
};
