import type {MenuProps} from 'antd';
import {Button, Dropdown, Row, Space, Typography} from 'antd';
import {RiArrowDownSFill} from 'react-icons/ri';

import UserAvatar from '../UserAvatar';
import type {GlobalRoleMap, PermissionMember, RoleRecord} from './types';

import {useAuthContext, useOrgContext} from '@unpod/providers';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import {getPostAllowedRoles, isShareBtnAccessAllowed,} from '@unpod/helpers/PermissionHelper';
import {maskEmail} from '@unpod/helpers/StringHelper';

type PostMemberRowProps = {
  member: PermissionMember;
  onRemoveInvitedMember: (email: string) => void;
  onUpdateInvitedMember: (member: PermissionMember) => void;
};

const PostMemberRow = ({
                         member,
                         onRemoveInvitedMember,
                         onUpdateInvitedMember,
                       }: PostMemberRowProps) => {
  const {user, globalData, activeOrg} = useAuthContext();
  const {activeSpace} = useOrgContext();

  const roles = (globalData.roles as GlobalRoleMap) || {};
  const currentPostUsers = activeSpace?.users || [];

  const onRoleChange: MenuProps['onClick'] = (item) => {
    const nextKey = String(item.key);

    if (nextKey === 'remove-access') {
      onRemoveInvitedMember(member.email || member.user_email || '');
      return;
    }

    if (nextKey !== 'divider') {
      onUpdateInvitedMember({...member, role_code: nextKey, role: nextKey});
    }
  };

  const getRoleList = (): MenuProps['items'] => {
    const roleData = (roles.space || roles.post || []) as RoleRecord[] | undefined;

    const allowedRoles = getPostAllowedRoles(
      roleData || [],
      currentPostUsers,
      user,
    );

    const roleList: NonNullable<MenuProps['items']> = allowedRoles
      .filter((item) => !!item.role_code)
      .map((item) => ({
        key: item.role_code || ACCESS_ROLE.VIEWER,
        label: String(item.role_name || item.role_code || ACCESS_ROLE.VIEWER),
      }));

    if (roleList.length > 1 || !member.joined) {
      roleList.push({type: 'divider'});
    }

    if (isShareBtnAccessAllowed(activeOrg, undefined, activeSpace)) {
      roleList.push({
        key: 'remove-access',
        label: 'Remove access',
        danger: true,
      });
    }

    return roleList;
  };

  const currentRoleName =
    ((roles.space || []).find((item) => item.role_code === member.role_code)
      ?.role_name as string | undefined) || ACCESS_ROLE.VIEWER;

  return (
    <Row justify="space-between" align="middle">
      <Space>
        <UserAvatar user={member}/>
        <Space orientation="vertical" size={0}>
          {member.full_name ? (
            <Typography.Text
              type={member.joined ? undefined : 'secondary'}
              style={{marginBottom: -4, display: 'block'}}
            >
              {member.full_name}
            </Typography.Text>
          ) : null}

          <Typography.Text type={member.joined ? undefined : 'secondary'}>
            {maskEmail(member.email || member.user_email || '')}
          </Typography.Text>
        </Space>
      </Space>

      {member.role === ACCESS_ROLE.OWNER ? (
        <Typography.Text style={{marginRight: 24}}>Owner</Typography.Text>
      ) : (
        <Dropdown
          menu={{
            items: getRoleList(),
            onClick: onRoleChange,
          }}
          trigger={['click']}
        >
          <Button>
            <Space>
              {currentRoleName}
              <RiArrowDownSFill
                fontSize={20}
                style={{
                  marginRight: -5,
                }}
              />
            </Space>
          </Button>
        </Dropdown>
      )}
    </Row>
  );
};

export default PostMemberRow;
