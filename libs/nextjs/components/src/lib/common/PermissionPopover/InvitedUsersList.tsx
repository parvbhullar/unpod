import {Space, Typography} from 'antd';
import {useIntl} from 'react-intl';

import MemberRow from './MemberRow';
import type {InvitedUsersListProps} from './types';

import AppScrollbar from '../../third-party/AppScrollbar';

const InvitedUsersList = ({
                            type,
                            currentData,
                            userList,
                            onRemoveInvitedMember,
                            onUpdateInvitedMember,
                          }: InvitedUsersListProps) => {
  const {formatMessage} = useIntl();

  return (
    <>
      {userList.length > 0 ? (
        <AppScrollbar
          style={{
            maxHeight: 'calc(100vh - 350px)',
          }}
        >
          <Space
            orientation="vertical"
            size="middle"
            style={{
              display: 'flex',
              margin: '16px 0 20px',
            }}
          >
            {userList.map((member, index) => (
              <MemberRow
                key={member.email || member.user_email || index}
                currentData={currentData}
                member={member}
                type={type}
                onRemoveInvitedMember={onRemoveInvitedMember}
                onUpdateInvitedMember={onUpdateInvitedMember}
              />
            ))}
          </Space>
        </AppScrollbar>
      ) : (
        <Typography.Paragraph>
          {formatMessage({id: 'common.noUser'})}
        </Typography.Paragraph>
      )}
    </>
  );
};

export default InvitedUsersList;
