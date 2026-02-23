'use client';
import React, {useMemo, useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Dropdown, Row, Select, Space, Typography} from 'antd';
import {RiArrowDownSFill} from 'react-icons/ri';
import {StyledFormContainer, StyledPopoverWrapper, StyledSpace,} from './index.styled';
import {MdClear} from 'react-icons/md';
import {SHARED_OPTIONS} from './data';
import {useAuthContext, useOrgContext} from '@unpod/providers';
import AppSelect from '../../antd/AppSelect';
import {EMAIL_REGX} from '@unpod/constants';
import {ACCESS_ROLE} from '@unpod/constants/AppEnums';
import {getPostAllowedRoles, isEditAccessAllowed,} from '@unpod/helpers/PermissionHelper';
import PostMemberRow from './PostMemberRow';
import AppScrollbar from '../../third-party/AppScrollbar';
import UserAvatar from '../UserAvatar';
import {AppPopover} from '../../antd';
import {useIntl} from 'react-intl';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';

const PostPermissionPopover = ({
                                 title,
                                 open,
                                 setOpen,
                                 placement,
                                 linkShareable,
                                 userList,
                                 setUserList,
                                 ...restProps
                               }) => {
  const {currentSpace, currentPost, orgUsers} = useOrgContext();
  // console.log('currentSpace', currentSpace, currentPost, orgUsers)
  const {user, globalData} = useAuthContext();
  const {roles} = globalData;
  const {formatMessage} = useIntl();

  const [shareType, setShareType] = useState(
    currentSpace?.is_private_domain ? 'link' : 'shared',
  );
  const [emails, setEmails] = useState([]);
  const [selectedRole, setSelectedRole] = useState('viewer');

  const selectedShareType = useMemo(() => {
    return SHARED_OPTIONS.find((item) => item.key === shareType);
  }, [shareType]);

  const onRemoveInvitedMember = (email) => {
    const newMembers = userList.filter((item) => item.email !== email);
    setUserList(newMembers);
  };
  const onUpdateInvitedMember = (member) => {
    const newMembers = userList.map((item) =>
      item.email === member.email ? member : item,
    );
    setUserList(newMembers);
  };

  const hidePopover = () => {
    setOpen(false);
  };

  const onChangeShareType = (item) => {
    setShareType(item.key);
  };

  const onEmailChange = (newEmails) => {
    setEmails(newEmails.filter((email) => EMAIL_REGX.test(email)));
  };

  const onAddClick = () => {
    const newUsers = emails.map((email) => ({
      email,
      role_code: selectedRole,
    }));

    setUserList([...userList, ...newUsers]);
    setEmails([]);
  };

  return (
    <AppPopover
      content={
        <StyledPopoverWrapper>
          <StyledFormContainer>
            <AppSelect
              mode="tags"
              placeholder={formatMessage({id: 'form.enterEmails'})}
              style={{flex: 1}}
              value={emails}
              onChange={onEmailChange}
              allowClear
              optionLabelProp="value"
              filterOption={(input, option) =>
                (option?.label ?? '')
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }
            >
              {orgUsers?.map((orgUser, index) => (
                <Select.Option
                  key={index}
                  value={orgUser.user_email}
                  label={`${orgUser.full_name} ${orgUser.user_email}`}
                >
                  <Space>
                    <UserAvatar user={orgUser}/>
                    <Space direction="vertical" size={0}>
                      {orgUser?.full_name && (
                        <Typography.Text
                          type={'secondary'}
                          style={{marginBottom: -4, display: 'block'}}
                        >
                          {orgUser?.full_name}
                        </Typography.Text>
                      )}
                      <Typography.Text type={'secondary'}>
                        {orgUser.user_email}
                      </Typography.Text>
                    </Space>
                  </Space>
                </Select.Option>
              ))}
            </AppSelect>
            <AppSelect
              placeholder="Role"
              value={selectedRole}
              onChange={setSelectedRole}
              style={{width: 100}}
            >
              {getPostAllowedRoles(
                currentPost ? roles?.post : roles?.space || [],
                currentPost ? currentPost?.users : currentSpace?.users,
                user,
              )?.map((role, index) => {
                if (role.role_code !== ACCESS_ROLE.OWNER) {
                  return (
                    <Select.Option key={index} value={role.role_code}>
                      {role.role_name}
                    </Select.Option>
                  );
                }
                return null;
              })}
            </AppSelect>

            <Button
              type="primary"
              onClick={onAddClick}
              disabled={!selectedRole || emails.length === 0}
            >
              Add
            </Button>
          </StyledFormContainer>
          {userList.length > 0 ? (
            <AppScrollbar
              style={{
                // minHeight: 230,
                height: '380px',
                maxHeight: 'calc(100vh - 300px)',
              }}
            >
              <Space
                direction={'vertical'}
                size="middle"
                css={`
                  display: flex;
                  margin: 16px 0 20px;
                `}
              >
                {userList.map((member, index) => (
                  <PostMemberRow
                    key={index}
                    member={member}
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

          {linkShareable &&
          isEditAccessAllowed(undefined, currentPost, undefined) ? (
            <Dropdown
              menu={{
                items: getLocalizedOptions(SHARED_OPTIONS, formatMessage),
                onClick: onChangeShareType,
              }}
              trigger={['click']}
            >
              <div>
                <StyledSpace>
                  <span>{selectedShareType.image}</span>
                  <div>
                    <Space>
                      <Typography.Text strong>
                        {formatMessage({id: selectedShareType.label})}
                      </Typography.Text>
                      <RiArrowDownSFill fontSize={24}/>
                    </Space>
                    <Typography.Paragraph className={'mb-0'}>
                      {formatMessage({id: selectedShareType.description})}
                    </Typography.Paragraph>
                  </div>
                </StyledSpace>
              </div>
            </Dropdown>
          ) : isEditAccessAllowed(undefined, currentPost, undefined) ? (
            <StyledSpace>
              <span>{selectedShareType.image}</span>
              <div>
                <Space>
                  <Typography.Text strong>
                    {formatMessage({id: selectedShareType.label})}
                  </Typography.Text>
                </Space>
                <Typography.Paragraph className={'mb-0'}>
                  {formatMessage({id: selectedShareType.description})}
                </Typography.Paragraph>
              </div>
            </StyledSpace>
          ) : null}

          <Row justify="end">
            <Typography.Link onClick={hidePopover}>
              {formatMessage({id: 'common.done'})}
            </Typography.Link>
          </Row>
        </StyledPopoverWrapper>
      }
      title={
        <Row justify="space-between" align="middle">
          <Typography.Text>{title}</Typography.Text>
          <MdClear
            fontSize={24}
            css={'cursor: pointer'}
            onClick={hidePopover}
          />
        </Row>
      }
      placement={placement}
      showArrow={false}
      open={open}
      {...restProps}
    />
  );
};

PostPermissionPopover.propTypes = {
  title: PropTypes.string,
  linkShareable: PropTypes.bool,
  open: PropTypes.bool,
  currentSpace: PropTypes.object,
  setOpen: PropTypes.func,
  onPermissionChange: PropTypes.func,
  placement: PropTypes.string,
  userList: PropTypes.array,
  setUserList: PropTypes.func,
};

PostPermissionPopover.defaultProps = {
  title: 'Share your thread!',
  placement: 'topLeft',
  open: false,
  linkShareable: false,
  userList: [],
};

export default React.memo(PostPermissionPopover);
