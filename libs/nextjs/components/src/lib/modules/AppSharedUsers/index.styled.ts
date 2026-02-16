import styled from 'styled-components';
import { Avatar } from 'antd';

export const StyledAvatarGroup = styled(Avatar.Group)`
  display: flex;
  .ant-avatar {
    margin: 0 auto !important;

    &:not(:first-child) {
      margin-inline-start: -14px !important;
    }
  }
`;

export const StyledUsersContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  max-width: 240px;
`;
