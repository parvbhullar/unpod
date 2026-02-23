import React, {useEffect, useMemo, useState} from 'react';
import PropTypes from 'prop-types';
import {Badge, Button, Col, Dropdown, Form, Row, Space, Tooltip, Typography, Upload,} from 'antd';
import {
  MdArrowForward,
  MdDelete,
  MdDeleteOutline,
  MdOutlineAttachment,
  MdOutlineEdit,
  MdOutlineWorkspaces,
} from 'react-icons/md';
import {BsFillFileEarmarkPersonFill} from 'react-icons/bs';
import AppImage from '../../next/AppImage';
import {AskAttachmentTypes, PERMISSION_TYPES} from '@unpod/constants';
import {postDataApi, uploadDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import {ACCESS_ROLE, POST_CONTENT_TYPE, POST_TYPE,} from '@unpod/constants/AppEnums';
import AppLoader from '../AppLoader';
import AppPopconfirm from '../../antd/AppPopconfirm';
import PostPermissionPopover from '../PermissionPopover/PostPermissionPopover';
import AppSuperbookInputs from './AppSuperbookInputs';
import {
  StyledActionBtn,
  StyledAppLabel,
  StyledBlock,
  StyledBlockActions,
  StyledBottomBar,
  StyledContainer,
  StyledIconWrapper,
  StyledInput,
  StyledTopBar,
  StylesLogoWrapper,
} from './index.styled';
import {getDateObject} from '@unpod/helpers/DateHelper';
import {getJsonString} from '@unpod/helpers/StringHelper';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';
import {useIntl} from 'react-intl';

const {Text} = Typography;
const {Item, useForm} = Form;

const ALLOWED_TYPES = '.xls, .xlsx, .csv';

const AppSuperbookInputBlock = ({
                                  superBook,
                                  inputSchema,
                                  isEdit,
                                  onEdit,
                                  onDelete,
                                  onRunFinished,
                                }) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {isAuthenticated, user} = useAuthContext();
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const [description, setDescription] = useState(null);
  const [privacyType, setPrivacyType] = useState('public');
  const [currentPrivacy, setCurrentPrivacy] = useState(null);
  const [spaceList, setSpaceList] = useState([]);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [open, setOpen] = useState(false);
  const [userList, setUserList] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initialData = {};
    for (const item of inputSchema) {
      if (item.type === 'date') {
        initialData[item.name] = item.defaultValue
          ? getDateObject(item.defaultValue, 'YYYY-MM-DD')
          : null;
      } else if (item.type === 'time') {
        initialData[item.name] = item.defaultValue
          ? getDateObject(item.defaultValue, 'HH:mm:ss')
          : null;
      } else if (item.type === 'datetime') {
        initialData[item.name] = item.defaultValue
          ? getDateObject(item.defaultValue, 'YYYY-MM-DD HH:mm:ss')
          : null;
      } else if (item.type === 'json') {
        initialData[item.name] = item.defaultValue
          ? getJsonString(item.defaultValue)
          : null;
      } else {
        initialData[item.name] = item.defaultValue || null;
      }
    }

    form.setFieldsValue(initialData);
  }, [inputSchema]);

  useEffect(() => {
    if (user) {
      if (user.space) {
        const spaces = [];

        user.space.forEach((item) => {
          if (item.role !== 'viewer') {
            spaces.push({
              key: item.token,
              label: item.name,
              token: item.token,
            });
          }
        });
        setSpaceList(spaces);

        if (user.active_space) {
          setSelectedSpace(
            spaces.find((space) => space.token === user.active_space.token),
          );
        }
      }
    }
  }, [user]);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType),
    );
  }, [privacyType]);

  const onSpaceChange = (option) => {
    setSelectedSpace(spaceList.find((space) => space.key === option.key));
  };

  const onShareChange = (option) => {
    setPrivacyType(option.key);

    if (option.key === 'shared') {
      setOpen(true);
    }
  };

  const handleAttachmentChange = (file) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      AskAttachmentTypes &&
      !AskAttachmentTypes.includes(extension) &&
      (!file.type ||
        (!AskAttachmentTypes.includes(file.type) &&
          !AskAttachmentTypes.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(`File type is now allowed`);
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event, file) => {
    event.stopPropagation();
    setAttachments((prevState) =>
      prevState.filter((item) => item.uid !== file.uid),
    );
  };

  const attachmentsList = useMemo(() => {
    return attachments.map((item) => ({
      key: item.uid,
      label: (
        <Row justify="space-between" align="middle">
          <Text style={{marginRight: 5}}>{item.name}</Text>
          <MdDelete
            fontSize={18}
            onClick={(event) => onAttachmentRemove(event, item)}
          />
        </Row>
      ),
    }));
  }, [attachments]);

  const resetForm = () => {
    setPrivacyType('public');
    setUserList([]);

    const initialData = {};
    for (const item of inputSchema) {
      if (item.type === 'date') {
        initialData[item.name] = item.defaultValue
          ? getDateObject(item.defaultValue, 'YYYY-MM-DD')
          : null;
      } else if (item.type === 'time') {
        initialData[item.name] = item.defaultValue
          ? getDateObject(item.defaultValue, 'HH:mm:ss')
          : null;
      } else if (item.type === 'datetime') {
        initialData[item.name] = item.defaultValue
          ? getDateObject(item.defaultValue, 'YYYY-MM-DD HH:mm:ss')
          : null;
      } else if (item.type === 'json') {
        initialData[item.name] = item.defaultValue
          ? getJsonString(item.defaultValue)
          : null;
      } else {
        initialData[item.name] = item.defaultValue || null;
      }
    }
    form.resetFields();
    form.setFieldsValue(initialData);
  };

  const uploadAttachments = (callbackFun, payload) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi(`media/upload-multiple/`, infoViewActionsContext, formData)
      .then((res) => {
        payload.files = res.data;
        setAttachments([]);
        callbackFun(payload);
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const savePost = (payload) => {
    const requestUrl = `threads/${selectedSpace?.token}/`;

    postDataApi(requestUrl, infoViewActionsContext, payload)
      .then((res) => {
        resetForm();
        infoViewActionsContext.showMessage(res.message);
        setLoading(false);
        onRunFinished?.(res.data);
      })
      .catch((error) => {
        infoViewActionsContext.showError(error.message);
        setLoading(false);
      });
  };

  const onFinish = (values) => {
    if (values || attachments?.length) {
      if (selectedSpace?.token) {
        setLoading(true);

        const payload = {
          content:
            Object.keys(values).length > 0 ? JSON.stringify(values) : null,
          post_type: POST_TYPE.NOTEBOOK,
          content_type: POST_CONTENT_TYPE.TEXT,
          privacy_type: privacyType,
          pilot: superBook?.handle,
          knowledge_bases: [],
          user_list:
            privacyType === 'shared'
              ? userList.filter((user) => user.role_code !== ACCESS_ROLE.OWNER)
              : [],
          tags: [],
        };

        if (attachments?.length) {
          uploadAttachments(savePost, payload);
        } else {
          savePost(payload);
        }
      } else {
        infoViewActionsContext.showError('Please select a space');
      }
    }
  };

  return (
    <Form onFinish={onFinish} form={form}>
      <StyledBlock>
        <StyledTopBar>
          <Space size="small" align="center">
            {superBook?.logo ? (
              <StylesLogoWrapper>
                <AppImage
                  src={`${superBook.logo}?tr=w-100,h-100`}
                  alt="logo"
                  height={100}
                  width={100}
                  layout="fill"
                  objectFit="cover"
                />
              </StylesLogoWrapper>
            ) : (
              <StyledIconWrapper>
                <BsFillFileEarmarkPersonFill fontSize={18}/>
              </StyledIconWrapper>
            )}

            <StyledAppLabel strong>{superBook.name}</StyledAppLabel>
          </Space>

          {isEdit && (
            <StyledBlockActions>
              <Tooltip title="Edit">
                <StyledActionBtn onClick={onEdit}>
                  <MdOutlineEdit fontSize={20}/>
                </StyledActionBtn>
              </Tooltip>

              {inputSchema.length > 0 && (
                <AppPopconfirm
                  title="Delete block"
                  description="Are you sure to delete this block?"
                  onConfirm={onDelete}
                  okText="Yes"
                  cancelText="No"
                >
                  <Tooltip title="Delete">
                    <StyledActionBtn>
                      <MdDeleteOutline fontSize={20}/>
                    </StyledActionBtn>
                  </Tooltip>
                </AppPopconfirm>
              )}
            </StyledBlockActions>
          )}
        </StyledTopBar>

        <StyledContainer>
          <Row gutter={16}>
            {inputSchema.map((item, index) =>
              item.type === 'checkboxes' ? (
                <Col key={index} xs={24} sm={24} md={24}>
                  <AppSuperbookInputs item={item}/>
                </Col>
              ) : item.type === 'textarea' || item.type === 'json' ? (
                <Col key={index} xs={24} sm={24} md={24}>
                  <AppSuperbookInputs item={item}/>
                </Col>
              ) : (
                <Col key={index} xs={24} sm={12} md={8}>
                  <AppSuperbookInputs item={item}/>
                </Col>
              ),
            )}
          </Row>

          <Item name="content">
            <StyledInput
              placeholder={
                (inputSchema || []).length > 0
                  ? 'Instructions (Optional)'
                  : `Ask me to do anything...`
              }
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={200}
              variant="borderless"
              autoSize={{minRows: 2, maxRows: 3}}
              size="large"
            />
          </Item>
        </StyledContainer>

        <StyledBottomBar>
          {isAuthenticated ? (
            <Space size="small" align="center" wrap>
              <Dropdown
                menu={{
                  items: spaceList,
                  onClick: onSpaceChange,
                  selectedKeys: selectedSpace?.key,
                  style: {maxHeight: 220, overflowY: 'auto'},
                }}
                trigger={['click']}
                arrow
              >
                <Button type="default">
                  <Space align="center">
                    <MdOutlineWorkspaces fontSize={21}/>

                    <span>
                      {selectedSpace?.label
                        ? selectedSpace.label.slice(0, 20).trim()
                        : 'Space'}
                    </span>
                  </Space>
                </Button>
              </Dropdown>

              <PostPermissionPopover
                open={open}
                setOpen={setOpen}
                userList={userList}
                setUserList={setUserList}
                placement="top"
              >
                <Dropdown
                  menu={{
                    items: getLocalizedOptions(PERMISSION_TYPES, formatMessage),
                    onClick: onShareChange,
                    selectedKeys: currentPrivacy?.key,
                  }}
                  trigger={['click']}
                  disabled={open}
                  arrow
                >
                  <Button type="default">
                    <Space align="center">
                      {currentPrivacy?.icon}
                      <span>
                        {currentPrivacy?.label
                          ? formatMessage({id: currentPrivacy.label})
                          : ''}
                      </span>
                    </Space>
                  </Button>
                </Dropdown>
              </PostPermissionPopover>
            </Space>
          ) : (
            <div/>
          )}

          <Space align="center">
            {/*<Text>Or Upload Bulk Tasks</Text>*/}
            <Upload
              name="files"
              accept={ALLOWED_TYPES}
              maxCount={10}
              beforeUpload={handleAttachmentChange}
              showUploadList={false}
              multiple
            >
              {attachments?.length > 0 ? (
                <Dropdown
                  menu={{
                    items: attachmentsList,
                  }}
                  trigger={['hover']}
                  placement="top"
                  arrow
                >
                  <Badge count={attachments?.length} offset={[-5, 2]}>
                    <Button
                      type={attachments?.length ? 'primary' : 'default'}
                      shape="circle"
                      icon={<MdOutlineAttachment fontSize={18}/>}
                    />
                  </Badge>
                </Dropdown>
              ) : (
                <Button
                  type={attachments?.length ? 'primary' : 'default'}
                  shape="circle"
                  icon={<MdOutlineAttachment fontSize={18}/>}
                />
              )}
            </Upload>

            <Button type="primary" shape="round" htmlType="submit">
              <Space>
                Run <MdArrowForward fontSize={18}/>
              </Space>
            </Button>
          </Space>
        </StyledBottomBar>
      </StyledBlock>

      {loading && <AppLoader/>}
    </Form>
  );
};

const {array, bool, func, object} = PropTypes;

AppSuperbookInputBlock.propTypes = {
  superBook: object,
  currentKb: object,
  inputSchema: array,
  isEdit: bool,
  onEdit: func,
  onDelete: func,
  onRunFinished: func,
};

export default AppSuperbookInputBlock;
