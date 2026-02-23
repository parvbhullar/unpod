import {AppSelect} from '@unpod/components/antd';
import {Avatar, Button, Card, Divider, Flex, Select, Typography} from 'antd';
import styled from 'styled-components';
import {DeleteOutlined, UserOutlined} from '@ant-design/icons';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';

const StyledUserList = styled.div`
  overflow: auto;
  height: 200px;
  max-width: 100%;
  width: 100%;
  border-radius: 8px;
  background: ${({theme}) => theme.palette.background.disabled};
`;

const UserCard = styled(Flex)`
  padding: 12px 16px;
  align-items: center;
`;

const StyledHeader = styled(Flex)`
  padding: 8px 16px;
  font-weight: 500;
  border-bottom: 1px solid;
  border-color: ${({theme}) => theme.palette.background.disabled};
`;

const NoUserFoundCard = styled(Card)`
  border-radius: 8px;
  background: ${({theme}) => theme.palette.background.disabled};
  text-align: center;
  padding: 24px;
`;

type SharedField = {
  email: string;
  role_code: string;
};

type SharedUserListProps = {
  sharedFields: SharedField[];
  handleDeleteField: (index: number) => void;
};

const SharedUserList = ({
                          sharedFields,
                          handleDeleteField,
                        }: SharedUserListProps) => {
  if (!sharedFields.length) {
    return (
      <NoUserFoundCard>
        <Typography.Paragraph type="secondary" style={{margin: 0}}>
          No users added yet. Please add users to share this workflow.
        </Typography.Paragraph>
      </NoUserFoundCard>
    );
  }

  return (
    <Card styles={{body: {padding: 0}}}>
      <StyledHeader justify="space-between">
        <Flex flex="1">User</Flex>
        <Flex flex="0.6" justify="center">
          Role
        </Flex>
        <Flex style={{width: '48px'}} justify="center">
          Action
        </Flex>
      </StyledHeader>
      <StyledUserList>
        {sharedFields.map((field, index) => (
          <div key={field.email}>
            <UserCard justify="space-between">
              <Flex flex="1" align="center" gap={12}>
                <Avatar icon={<UserOutlined/>} size="small"/>
                <Typography.Text ellipsis style={{maxWidth: '300px'}}>
                  {field.email}
                </Typography.Text>
              </Flex>
              <Flex flex="0.6" justify="center">
                <AppSelect
                  value={field.role_code}
                  placeholder="Role"
                  style={{width: '110px'}}
                  popupMatchSelectWidth={false}
                  disabled={true}
                >
                  <Select.Option value={ACCESS_ROLE.VIEWER}>
                    Viewer
                  </Select.Option>
                  <Select.Option value={ACCESS_ROLE.EDITOR}>
                    Editor
                  </Select.Option>
                </AppSelect>
              </Flex>
              <Flex style={{width: '48px'}} justify="center">
                <Button
                  type="text"
                  icon={<DeleteOutlined/>}
                  danger
                  onClick={() => handleDeleteField(index)}
                />
              </Flex>
            </UserCard>
            {index < sharedFields.length - 1 && (
              <Divider style={{margin: 0}}/>
            )}
          </div>
        ))}
      </StyledUserList>
    </Card>
  );
};

export default SharedUserList;
