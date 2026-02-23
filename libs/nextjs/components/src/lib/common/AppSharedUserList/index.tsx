import React, {useEffect, useState} from 'react';
import SharedUsersForm from './SharedUsersForm';
import {allowedDefaultRoles} from './constants';
import MemberItem from './MemberItem';
import AppList from '../AppList';
import {useIntl} from 'react-intl';
import {InviteMember} from '@unpod/constants';

type RoleOption = {
  key: string;
  label: string;
};

type AppSharedUserListProps = {
  users?: InviteMember[];
  onChangeUsers?: (users: InviteMember[]) => void;
  allowedRoles?: RoleOption[];
  emptyText?: string;
};

const AppSharedUserList: React.FC<AppSharedUserListProps> = ({
                                                               users,
                                                               onChangeUsers,
                                                               allowedRoles = allowedDefaultRoles,
                                                               emptyText,
                                                             }) => {
  const [selectedUsers, setSelectUsers] = useState(users || []);
  const {formatMessage} = useIntl();

  useEffect(() => {
    if (onChangeUsers) {
      onChangeUsers(selectedUsers);
    }
  }, [onChangeUsers, selectedUsers]);

  const onRemoveInvitedMember = (email: string) => {
    const newMembers = selectedUsers.filter((item) => item.email !== email);
    setSelectUsers(newMembers);
  };
  const onUpdateInvitedMember = (member: InviteMember) => {
    const newMembers = selectedUsers.map((item) =>
      item.email === member.email ? member : item,
    );
    setSelectUsers(newMembers);
  };

  const onAddUsers = (user: InviteMember[]) => {
    const newMembers = [...selectedUsers];
    user.forEach((u) => {
      const exists = newMembers.find((item) => item.email === u.email);
      if (!exists) {
        newMembers.push(u);
      }
    });
    setSelectUsers(newMembers);
  };

  return (
    <>
      <SharedUsersForm
        onAddUsers={onAddUsers}
        allowedRoles={allowedRoles}
        selectedUsers={selectedUsers}
      />

      <AppList
        emptyContainerStyle={{maxHeight: 100, minHeight: 100}}
        data={selectedUsers}
        noDataMessage={emptyText || formatMessage({id: 'common.noUser'})}
        renderItem={(member, index) => (
          <MemberItem
            key={index}
            member={member}
            onRemoveInvitedMember={onRemoveInvitedMember}
            onUpdateInvitedMember={onUpdateInvitedMember}
          />
        )}
      />
    </>
  );
};

export default AppSharedUserList;
