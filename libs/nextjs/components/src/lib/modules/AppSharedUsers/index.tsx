import { Fragment } from 'react';

import { Tooltip } from 'antd';
import { useMediaQuery } from 'react-responsive';
import { useAuthContext } from '@unpod/providers';
import UserAvatar from '../../common/UserAvatar';
import { StyledAvatarGroup, StyledUsersContainer } from './index.styled';
import { TabWidthQuery } from '@unpod/constants';

const avatarStyle = { margin: 4 };
const maxStyle = { cursor: 'pointer' };

const AppSharedUsers = ({ users = [] }: { users?: any[] }) => {
  const isTabletOrMobile = useMediaQuery(TabWidthQuery);
  const { isAuthenticated } = useAuthContext();
  const usersLength = users?.length || 0;
  const maxCount = isTabletOrMobile ? 1 : 4;

  return (
    isAuthenticated && (
      <StyledAvatarGroup max={{ count: maxCount, style: maxStyle }}>
        {users?.slice(0, maxCount).map((member, index) => (
          <UserAvatar key={index} user={member} style={avatarStyle} />
        ))}

        {usersLength > maxCount && (
          <Fragment>
            {users.slice(maxCount, usersLength - 1).map((member, index) => (
              <div key={index} />
            ))}

            <StyledUsersContainer>
              {users.slice(maxCount).map((member, index) => (
                <Tooltip key={index} title={member?.full_name} placement="top">
                  <UserAvatar user={member} style={avatarStyle} />
                </Tooltip>
              ))}
            </StyledUsersContainer>
          </Fragment>
        )}
      </StyledAvatarGroup>
    )
  );
};

export default AppSharedUsers;
