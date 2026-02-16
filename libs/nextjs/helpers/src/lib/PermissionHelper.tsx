import { ReactNode } from 'react';
import { ACCESS_ROLE, POST_TYPE } from '@unpod/constants';
import { RiUserSharedLine } from 'react-icons/ri';
import { MdLockOutline, MdPublic } from 'react-icons/md';

export const Permissions = {
  add: 'add',
  edit: 'edit',
  delete: 'delete',
  archive: 'archive',
  share_entity: 'share_entity',
  privacy_update: 'privacy_update',
  view_list: 'view_list',
  view_user_list: 'view_user_list',
  view_detail: 'view_detail',
  comment: 'comment',
  use_superpilot: 'use_superpilot',
  transfer_ownership: 'transfer_ownership',
} as const;

export type PermissionType = (typeof Permissions)[keyof typeof Permissions];

export type EntityWithOperations = {
  joined?: boolean;
  allowed_operations?: string[];
  privacy_type?: string;
  post_type?: string;
  users?: EntityUser[];
};

export type EntityUser = {
  email?: string;
  role?: string;
};

export type Role = {
  role_code?: string;
  [key: string]: unknown;
};

export type MenuItem = {
  key: string;
  label?: string;
  type?: string;
  danger?: boolean;
};

export const getOptionMenu = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): MenuItem[] => {
  let options: MenuItem[] = [];
  if (currentHub && currentHub?.joined) {
    if (isEditAccessAllowed(currentHub, undefined, undefined))
      options = [
        {
          key: 'hub_settings',
          label: 'Organization Settings',
        },
      ];
  } else if (currentPost && currentPost?.joined) {
    if (
      currentPost.post_type !== POST_TYPE.TASK &&
      currentPost.post_type !== POST_TYPE.ASK &&
      isEditAccessAllowed(undefined, currentPost, undefined)
    )
      options = [
        {
          key: 'edit_post',
          label: 'Edit Post',
        },
      ];
    if (isDeleteAccessAllowed(undefined, currentPost, undefined))
      options = options.concat([
        {
          key: 'divider',
          type: 'divider',
        },
        {
          key: 'delete_post',
          danger: true,
          label: 'Delete',
        },
      ]);
  } else if (currentSpace && currentSpace?.joined) {
    if (isEditAccessAllowed(undefined, undefined, currentSpace)) {
      options = [
        {
          key: 'edit_space',
          label: 'Edit Space',
        },
      ];
    }

    if (isArchiveAccessAllowed(undefined, undefined, currentSpace)) {
      options.push({
        key: 'divider',
        type: 'divider',
      });

      options.push({
        key: 'archive-space',
        label: 'Archive',
      });
    }
  }

  return options;
};

export const isPermissionAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
  permission: string,
): boolean => {
  if (currentHub && currentHub?.allowed_operations) {
    return currentHub.allowed_operations.includes(permission);
  } else if (currentPost && currentPost?.allowed_operations) {
    return currentPost.allowed_operations.includes(permission);
  } else if (currentSpace && currentSpace?.allowed_operations) {
    return currentSpace.allowed_operations.includes(permission);
  }
  return false;
};

export const isEditAccessAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.edit,
  );
};

export const isArchiveAccessAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.archive,
  );
};

export const isDeleteAccessAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.delete,
  );
};

export const isShareAccessAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.share_entity,
  );
};

export const isShareBtnAccessAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.view_detail,
  );
};

export const isPrivacyUpdateAllow = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.privacy_update,
  );
};

export const isViewDetailAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.view_detail,
  );
};

export const isAddAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.add,
  );
};

export const isSupperPilotAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.add,
  );
};

export const isCommentAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.comment,
  );
};

export const isTransferOwnershipAllowed = (
  currentHub: EntityWithOperations | null | undefined,
  currentPost: EntityWithOperations | null | undefined,
  currentSpace: EntityWithOperations | null | undefined,
): boolean => {
  return isPermissionAllowed(
    currentHub,
    currentPost,
    currentSpace,
    Permissions.transfer_ownership,
  );
};

export type ThreadWithUser = EntityWithOperations & {
  user?: { email?: string };
};

export type CurrentUser = {
  email?: string;
};

export const getThreadMenu = (
  thread: ThreadWithUser,
  user: CurrentUser | null | undefined,
): MenuItem[] => {
  const menu: MenuItem[] = [];
  if (
    thread.post_type !== POST_TYPE.TASK &&
    thread.post_type !== POST_TYPE.ASK &&
    isEditAccessAllowed(undefined, thread, undefined)
  ) {
    menu.push({
      label: 'Edit',
      key: 'edit',
    });
  }
  if (thread?.user?.email !== user?.email) {
    menu.push({
      label: 'Report',
      key: 'report',
    });
  }
  if (isDeleteAccessAllowed(undefined, thread, undefined)) {
    menu.push({
      label: 'Delete',
      key: 'delete',
      danger: true,
    });
  }
  return menu;
};

export const checkRoleChangeAllowed = (
  roles: Role[] = [],
  users: EntityUser[] = [],
  me: CurrentUser | null | undefined,
): boolean => {
  const role = users.find((user) => user.email === me?.email)?.role;
  return role === ACCESS_ROLE.OWNER || role === ACCESS_ROLE.EDITOR;
};

export const getSpaceAllowedRoles = (
  roles: Role[] = [],
  users: EntityUser[] = [],
  me: CurrentUser | null | undefined,
): Role[] => {
  let roleList: Role[] = [];
  const role = users.find((user) => user.email === me?.email)?.role;
  if (role === ACCESS_ROLE.OWNER) {
    roleList = roles;
  } else if (role === ACCESS_ROLE.EDITOR) {
    roleList = roles.filter((r) => r.role_code !== ACCESS_ROLE.OWNER);
  } else if (role === ACCESS_ROLE.VIEWER) {
    roleList = roles.filter(
      (r) =>
        r.role_code !== ACCESS_ROLE.OWNER && r.role_code !== ACCESS_ROLE.EDITOR,
    );
  }

  console.log('roleList', roleList, roles, users, role, me);
  return roleList;
};

export const getPostAllowedRoles = (
  roles: Role[] = [],
  users: EntityUser[] = [],
  me: CurrentUser | null | undefined,
): Role[] => {
  if (users.length === 0) return roles;
  let roleList: Role[] = [];

  const role = users.find((user) => user.email === me?.email)?.role;
  if (role === ACCESS_ROLE.OWNER || role === ACCESS_ROLE.EDITOR) {
    roleList = roles.filter((r) => r.role_code !== ACCESS_ROLE.OWNER);
  } else if (role === ACCESS_ROLE.VIEWER) {
    roleList = roles.filter(
      (r) =>
        r.role_code !== ACCESS_ROLE.OWNER && r.role_code !== ACCESS_ROLE.EDITOR,
    );
  }
  return roleList;
};

export const getPostIcon = (
  key = 'public',
  size = 16,
  className = '',
): ReactNode => {
  switch (key) {
    case 'private':
      return <MdLockOutline fontSize={size} className={className} />;
    case 'shared':
      return <RiUserSharedLine fontSize={size} className={className} />;
    default:
      return <MdPublic fontSize={size} className={className} />;
  }
};

export const getSharerText = (key: string): string => {
  switch (key) {
    case 'private':
      return 'Private';
    case 'shared':
      return 'Shared';
    case 'link':
      return 'Anyone with link';
    default:
      return 'Public';
  }
};
