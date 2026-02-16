import type { MenuProps } from 'antd';
import { Button, Dropdown, Row, Space, Typography } from 'antd';
import { RiArrowDownSFill } from 'react-icons/ri';
import UserAvatar from '../UserAvatar';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import { maskEmail } from '@unpod/helpers/StringHelper';

type Member = {
  email: string;
  role_code?: string;
  full_name?: string;
  joined?: boolean;
  role?: string;};

type MemberItemProps = {
  member: Member;
  onRemoveInvitedMember: (email: string) => void;
  onUpdateInvitedMember: (member: Member) => void;};

const MemberItem: React.FC<MemberItemProps> = ({
  member,
  onRemoveInvitedMember,
  onUpdateInvitedMember,
}) => {
  const onRoleChange: MenuProps['onClick'] = (item) => {
    if (item.key === 'remove-access') {
      onRemoveInvitedMember(member?.email);
    } else if (item.key !== 'divider') {
      onUpdateInvitedMember({ ...member, role_code: item.key });
    }
  };

  return (
    <Row
      justify="space-between"
      align="middle"
      style={{ marginTop: 6, marginBottom: 12 }}
    >
      <Space>
        <UserAvatar user={member} />
        <Space orientation="vertical" size={0}>
          {member?.full_name && (
            <Typography.Text
              type={member?.joined ? undefined : 'secondary'}
              style={{ marginBottom: -4, display: 'block' }}
            >
              {member?.full_name}
            </Typography.Text>
          )}
          <Typography.Text type={member?.joined ? undefined : 'secondary'}>
            {maskEmail(member.email)}
          </Typography.Text>
        </Space>
      </Space>

      {member?.role === ACCESS_ROLE.OWNER ? (
        <Typography.Text style={{ marginRight: 24 }}> Owner </Typography.Text>
      ) : (
        <Dropdown
          menu={{
            items: [
              {
                label: 'Editor',
                key: 'editor',
              },
              {
                label: 'Viewer',
                key: 'viewer',
              },
              {
                type: 'divider',
                key: 'divider',
              },
              {
                label: 'Remove access',
                key: 'remove-access',
                danger: true,
              },
            ],
            onClick: onRoleChange,
          }}
          trigger={['click']}
        >
          <Button style={{ textTransform: 'capitalize' }}>
            {member?.role_code}
            <RiArrowDownSFill fontSize={20} style={{ marginRight: -5 }} />
          </Button>
        </Dropdown>
      )}
    </Row>
  );
};

export default MemberItem;
