'use client';

import { useEffect, useState } from 'react';
import { Typography } from 'antd';
import { DownOutlined, UpOutlined } from '@ant-design/icons';

import {
  StyledRequestedAccessWrapper,
  StyledRequestedMember,
  StyledRequestedMembersWrapper,
} from './index.styled';
import RequestAccessRow from './RequestAccessRow';
import type {
  PermissionEntity,
  PermissionMember,
  RequestedUsersListProps,
} from './types';

import UserAvatar from '../UserAvatar';
import AppScrollbar from '../../third-party/AppScrollbar';

const normalizeRequestMembers = (
  accessRequest: PermissionEntity['access_request'] | undefined,
): PermissionMember[] => {
  return Array.isArray(accessRequest) ? accessRequest : [];
};

const RequestedUsersList = ({
  type,
  currentData,
  userList,
  setUserList,
  setCurrentData,
}: RequestedUsersListProps) => {
  const [requestMembers, setRequestMembers] = useState<PermissionMember[]>(
    normalizeRequestMembers(currentData?.access_request),
  );
  const [expandView, setExpandView] = useState<boolean>(
    requestMembers.length === 1,
  );

  useEffect(() => {
    const nextMembers = normalizeRequestMembers(currentData?.access_request);
    setRequestMembers(nextMembers);
  }, [currentData?.access_request]);

  const updateUsersList = (
    members: PermissionMember[],
    users: PermissionMember[],
  ): void => {
    setRequestMembers(members);

    setCurrentData({
      ...(currentData || {}),
      access_request: members,
      users,
    });
  };

  const onAcceptMemberRequest = (member: PermissionMember): void => {
    const members = requestMembers.filter((item) => item.email !== member.email);

    if (member.is_member) {
      const users = userList.map((user) =>
        user.email === member.email ? member : user,
      );
      updateUsersList(members, users);
      return;
    }

    const users = [member, ...userList];
    setUserList(users);
    updateUsersList(members, users);
  };

  const onDenyMemberRequest = (email: string): void => {
    const members = requestMembers.filter((item) => item.email !== email);
    updateUsersList(members, userList);
  };

  return (
    <AppScrollbar
      style={{
        maxHeight: 'calc(100vh - 350px)',
      }}
    >
      <StyledRequestedMembersWrapper>
        {requestMembers.length > 1 ? (
          <StyledRequestedMember>
            <UserAvatar user={requestMembers[0]} />
            <Typography.Text>
              <span className="bold">
                {requestMembers[0].full_name || requestMembers[0].email}{' '}
                {requestMembers[0].role === 'editor' ? '(Editor)' : 'Viewer'}
              </span>
              {' and '}
              <span className="bold">{requestMembers.length - 1}</span> people
              are asking to access this space
            </Typography.Text>
            {expandView ? (
              <DownOutlined onClick={() => setExpandView(!expandView)} />
            ) : (
              <UpOutlined onClick={() => setExpandView(!expandView)} />
            )}
          </StyledRequestedMember>
        ) : null}

        {requestMembers.length > 0 && expandView ? (
          <StyledRequestedAccessWrapper>
            {requestMembers.length > 1 ? (
              requestMembers.map((member) => (
                <RequestAccessRow
                  key={
                    member.email || member.user_email || member.request_token
                  }
                  type={type}
                  member={member}
                  currentData={currentData}
                  onAcceptMemberRequest={onAcceptMemberRequest}
                  onDenyMemberRequest={onDenyMemberRequest}
                />
              ))
            ) : (
              <RequestAccessRow
                type={type}
                member={requestMembers[0]}
                currentData={currentData}
                onAcceptMemberRequest={onAcceptMemberRequest}
                onDenyMemberRequest={onDenyMemberRequest}
              />
            )}
          </StyledRequestedAccessWrapper>
        ) : null}
      </StyledRequestedMembersWrapper>
    </AppScrollbar>
  );
};

export default RequestedUsersList;
