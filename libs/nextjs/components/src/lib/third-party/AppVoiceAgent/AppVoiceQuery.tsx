import React, {
  Fragment,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';
import PropTypes from 'prop-types';
import {
  Badge,
  Dropdown,
  Form,
  Row,
  Space,
  Tooltip,
  Typography,
  Upload,
} from 'antd';
import { MdArrowForward, MdDelete, MdOutlineAttachment } from 'react-icons/md';
import {
  localPostDataApi,
  postDataApi,
  uploadDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { useRouter } from 'next/navigation';
import { AskAttachmentTypes, PERMISSION_TYPES } from '@unpod/constants';
import PostPermissionPopover from '../../common/PermissionPopover/PostPermissionPopover';
import {
  ACCESS_ROLE,
  POST_CONTENT_TYPE,
  POST_TYPE,
} from '@unpod/constants/AppEnums';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { useOrgContext } from '@unpod/providers';
import AppLoader from '../../common/AppLoader';
import AppPilotPopover from '../../modules/AppPilotPopover';
import AppKbPopover from '../../modules/AppKbPopover';
import SendButton from '../../modules/AppQueryWindow/SendButton';
import {
  StyledBottomBar,
  StyledButton,
  StyledContainer,
  StyledIconButton,
  StyledInput,
  StyledMainContent,
  VoiceOverlay,
} from '../../modules/AppQueryWindow/index.styled';
import ContextView from '../../modules/AppQueryWindow/ContextView';
import {
  AgentConnectionProvider,
  useAgentConnection,
} from '@unpod/livekit/hooks/useAgentConnection';
import AgentView from '../../third-party/AppVoiceAgent/AgentView';
import { useIntl } from 'react-intl';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';

const { Item, useForm } = Form;
const { Text } = Typography;

const UserQuery = ({
  scheduleBtn,
  kbPopover,
  pilotPopover,
  hideAttachment,
  onDataSaved,
  isMySpace,
  defaultKbs,
  executionType,
  ref,
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { visitorId, isAuthenticated, user } = useAuthContext();
  const router = useRouter();
  const [form] = useForm();

  const [privacyType, setPrivacyType] = useState('private');
  const [loadingToken, setLoadingToken] = useState(false);
  const { roomToken, updateRoomToken } = useAgentConnection();
  const [currentPrivacy, setCurrentPrivacy] = useState(null);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [open, setOpen] = useState(false);
  const [context, setContext] = useState(null);
  const [query, setQuery] = useState(null);
  const [userList, setUserList] = useState([]);
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [pilot, setPilot] = useState(null);
  const [focus, setFocus] = useState(isMySpace ? 'my_space' : 'public');
  const { formatMessage } = useIntl();

  const inputRef = useRef(null);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType),
    );
  }, [privacyType]);

  useEffect(() => {
    if (user?.active_space) {
      setSelectedSpace(user.active_space);
    }
  }, [user]);

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
    if (isAuthenticated && selectedSpace?.token) {
      const requestUrl = `threads/${selectedSpace?.token}/`;

      postDataApi(requestUrl, infoViewActionsContext, payload)
        .then((res) => {
          // infoViewActionsContext.showMessage(res.message);
          setLoading(false);
          form.resetFields();
          setAttachments([]);
          setQuery(null);

          if (res.data.slug) {
            if (onDataSaved) {
              onDataSaved(res.data);
            } else {
              router.push(`/thread/${res.data.slug}/`);
            }
          }
        })
        .catch((error) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    } else {
      const requestUrl = `threads/anonymous/create/`;

      postDataApi(requestUrl, infoViewActionsContext, payload)
        .then((res) => {
          infoViewActionsContext.showMessage(res.message);
          setLoading(false);

          if (onDataSaved) {
            onDataSaved(res.data);
          } else {
            router.push(`/thread/${res.data.slug}/`);
          }
        })
        .catch((error) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    }
  };

  const getPayload = (values) => {
    let payload = {
      // title: title,
      content: values.content || '',
      data: context?.payload || '',
      post_type: POST_TYPE.ASK,
      content_type: POST_CONTENT_TYPE.TEXT,
      session_user: visitorId,
      focus: focus,
      pilot: pilot?.slug || '',
      execution_type: executionType || '',
      knowledge_bases: defaultKbs
        ? [...defaultKbs, ...knowledgeBases]
        : knowledgeBases,
    };

    if (isAuthenticated) {
      const { content, ...rest } = values;
      payload = {
        // title: title,
        content: content || '',
        data: context?.payload || '',
        post_type: POST_TYPE.ASK,
        content_type: POST_CONTENT_TYPE.TEXT,
        privacy_type: privacyType,
        focus: focus,
        pilot: pilot?.slug || '',
        execution_type: executionType || '',
        knowledge_bases: defaultKbs
          ? [...defaultKbs, ...knowledgeBases]
          : knowledgeBases,
        user_list:
          privacyType === 'shared'
            ? userList.filter((user) => user.role_code !== ACCESS_ROLE.OWNER)
            : [],
        ...rest,
      };
    }
    return payload;
  };

  const onQuerySubmit = (values) => {
    if (values.content || attachments?.length) {
      setLoading(true);
      const payload = getPayload(values);

      if (attachments?.length) {
        uploadAttachments(savePost, payload);
      } else {
        savePost(payload);
      }
    } else {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.enterQueryFirst' }),
      );
    }
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
      infoViewActionsContext.showError(
        formatMessage({ id: 'upload.errorInvalidFileType' }),
      );
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

  useImperativeHandle(ref, () => {
    return {
      setActivePilot(newPilot) {
        console.log('newPilot', newPilot);
      },
      askQuery(values) {
        onQuerySubmit(values);
      },
      resetContext() {
        setContext(null);
        setQuery(null);
        form.setFieldValue('content', null);
      },
      setContext(content, context) {
        if (content) {
          setQuery(content);
          form.setFieldValue('content', content);
          inputRef.current.focus({
            preventScroll: true,
          });
        }

        setContext(context);
      },
    };
  }, [onQuerySubmit, form, inputRef]);

  const attachmentsList = useMemo(() => {
    return attachments.map((item) => ({
      key: item.uid,
      label: (
        <Row justify="space-between" align="middle">
          <Text style={{ marginRight: 5 }}>{item.name}</Text>
          <MdDelete
            fontSize={18}
            onClick={(event) => onAttachmentRemove(event, item)}
          />
        </Row>
      ),
    }));
  }, [attachments]);

  const onContextClose = () => {
    setContext(null);
  };

  const onStartVoice = async () => {
    setLoadingToken(true);

    try {
      const values = form.getFieldsValue();
      const payload = getPayload(values);
      const requestUrl = `/api/token/livekit/`;

      console.log('🔑 Generating token via local API...');
      const startTime = performance.now();

      const data = await localPostDataApi(requestUrl, infoViewActionsContext, {
        ...payload,
        space_token: selectedSpace?.token,
      });

      const token = data.accessToken;
      const duration = (performance.now() - startTime).toFixed(2);
      console.log(`✅ Token generated successfully in ${duration}ms`);

      updateRoomToken(token);
      setLoadingToken(false);

      return token;
    } catch (error) {
      console.error('❌ Token generation failed:', error);
      infoViewActionsContext.showError(error.message);
      setLoadingToken(false);
      throw error;
    }
  };
  return (
    <Fragment>
      <Form onFinish={onQuerySubmit} form={form}>
        <StyledContainer>
          <StyledMainContent>
            {context && (
              <ContextView context={context} onContextClose={onContextClose} />
            )}

            <Item name="content">
              <StyledInput
                placeholder={formatMessage({ id: 'common.askAnything' })}
                variant="borderless"
                autoSize={{ minRows: 2, maxRows: 10 }}
                size="large"
                onChange={(e) => setQuery(e.target.value)}
                onPressEnter={form.submit}
                ref={inputRef}
              />
            </Item>
          </StyledMainContent>

          <StyledBottomBar>
            <Space align="center" wrap>
              {pilotPopover && (
                <AppPilotPopover
                  pilot={pilot}
                  setPilot={setPilot}
                  focus={focus}
                  setFocus={setFocus}
                  isMySpace={isMySpace}
                />
              )}

              {isAuthenticated && (
                <Fragment>
                  {kbPopover && (
                    <AppKbPopover
                      knowledgeBases={knowledgeBases}
                      setKnowledgeBases={setKnowledgeBases}
                    />
                  )}

                  <PostPermissionPopover
                    open={open}
                    setOpen={setOpen}
                    userList={userList}
                    setUserList={setUserList}
                    placement="top"
                  >
                    <Dropdown
                      menu={{
                        items: getLocalizedOptions(
                          PERMISSION_TYPES,
                          formatMessage,
                        ),
                        onClick: onShareChange,
                        selectedKeys: currentPrivacy?.key,
                      }}
                      trigger={['click']}
                      disabled={open}
                      arrow
                    >
                      <Tooltip
                        title={formatMessage({ id: currentPrivacy?.label })}
                      >
                        <StyledIconButton type="text" shape="round">
                          {currentPrivacy?.iconOnly}
                          {/*{currentPrivacy?.label}*/}
                        </StyledIconButton>
                      </Tooltip>
                    </Dropdown>
                  </PostPermissionPopover>
                </Fragment>
              )}
            </Space>

            <Space size="small" align="center" wrap>
              {!hideAttachment && (
                <Upload
                  name="files"
                  accept={AskAttachmentTypes}
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
                        <StyledIconButton type="text" shape="round">
                          <MdOutlineAttachment fontSize={24} />
                        </StyledIconButton>
                      </Badge>
                    </Dropdown>
                  ) : (
                    <StyledIconButton type="text" shape="round">
                      <MdOutlineAttachment fontSize={24} />
                    </StyledIconButton>
                  )}
                </Upload>
              )}

              {scheduleBtn ? (
                <SendButton
                  attachments={attachments}
                  query={query}
                  onSchedule={(values) =>
                    onQuerySubmit({ ...values, content: query })
                  }
                />
              ) : query ? (
                <StyledButton type="primary" shape="round" htmlType="submit">
                  {formatMessage({ id: 'common.submit' })}{' '}
                  <MdArrowForward fontSize={18} />
                </StyledButton>
              ) : (
                <StyledButton
                  type="primary"
                  shape="round"
                  loading={loadingToken}
                  onClick={onStartVoice}
                >
                  {formatMessage({ id: 'common.talk' })}{' '}
                  <MdArrowForward fontSize={18} />
                </StyledButton>
              )}
            </Space>
          </StyledBottomBar>

          {roomToken && (
            <VoiceOverlay show={roomToken}>
              <AgentView
                token={roomToken}
                // config={{
                //   circular: true,
                //   agent: {
                //     image: 'https://www.debutinfotech.com/_next/image?url=https%3A%2F%2Fblogs.debutinfotech.com%2Fwp-content%2Fuploads%2F2025%2F01%2FAi-agent-architecture.jpg&w=1920&q=85',
                //     color:"#0062ff",
                //     activeColor: '#ff8c00',
                //   },
                //   local: {
                //     image: 'https://www.w3schools.com/howto/img_avatar.png',
                //     color: '#8a2be2',
                //     activeColor: '#ff4500',
                //   },
                // }}
              />
            </VoiceOverlay>
          )}
        </StyledContainer>
      </Form>

      {loading && <AppLoader />}
    </Fragment>
  );
};
UserQuery.displayName = 'UserQuery';

const { array, bool, func, string } = PropTypes;

UserQuery.propTypes = {
  scheduleBtn: bool,
  kbPopover: bool,
  pilotPopover: bool,
  hideAttachment: bool,
  onDataSaved: func,
  isMySpace: bool,
  defaultKbs: array,
  executionType: string,
};

const AppQueryWindow = () => {
  return (
    <AgentConnectionProvider>
      <UserQuery />
    </AgentConnectionProvider>
  );
};

export default AppQueryWindow;
