import type {Ref} from 'react';
import {Fragment, useEffect, useImperativeHandle, useMemo, useRef, useState,} from 'react';

import {Badge, Button, Dropdown, Form, Row, Space, Typography, Upload,} from 'antd';
import {MdDelete, MdOutlineAttachment} from 'react-icons/md';
import {RiVoiceprintLine} from 'react-icons/ri';
import {SendOutlined} from '@ant-design/icons';
import {postDataApi, uploadDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {useRouter} from 'next/navigation';
import {AskAttachmentTypes} from '@unpod/constants';
import {ACCESS_ROLE, POST_CONTENT_TYPE, POST_TYPE,} from '@unpod/constants/AppEnums';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import AppLoader from '../../common/AppLoader';
import SendButton from './SendButton';
import ContextView from './ContextView';
import {StyledBottomBar, StyledContainer, StyledInput, StyledMainContent,} from './index.styled';
import {useIntl} from 'react-intl';

const {Item, useForm} = Form;
const {Text} = Typography;

type AppQueryWindowProps = {
  scheduleBtn?: boolean;
  hideAttachment?: boolean;
  onDataSaved?: (data: any) => void;
  isMySpace?: boolean;
  defaultKbs?: string[];
  executionType?: string;
  pilotPopover?: boolean;
  ref?: Ref<any>;
};

const AppQueryWindow = ({
                          scheduleBtn,
                          hideAttachment,
                          onDataSaved,
                          isMySpace,
                          defaultKbs,
                          executionType,
                          pilotPopover,
                          ref,
                        }: AppQueryWindowProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {visitorId, isAuthenticated, user} = useAuthContext();
  const {formatMessage} = useIntl();

  const router = useRouter();
  const [form] = useForm();

  const [privacyType] = useState('private');
  const [selectedSpace, setSelectedSpace] = useState<any | null>(null);
  const [context, setContext] = useState<any | null>(null);
  const [query, setQuery] = useState<string | null>(null);
  const [userList] = useState<any[]>([]);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [knowledgeBases] = useState<string[]>([]);
  const [pilot] = useState<any | null>(null);
  const [focus] = useState(isMySpace ? 'my_space' : 'public');

  const inputRef = useRef<any>(null);

  useEffect(() => {
    if (user?.active_space) {
      setSelectedSpace(user.active_space);
    }
  }, [user]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // console.log('user: ', user);

  const uploadAttachments = (
    callbackFun: (payload: Record<string, any>) => void,
    payload: Record<string, any>,
  ) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi(`media/upload-multiple/`, infoViewActionsContext, formData)
      .then((res: any) => {
        payload.files = res.data;
        setAttachments([]);
        callbackFun(payload);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const savePost = (payload: Record<string, any>) => {
    if (isAuthenticated && selectedSpace?.token) {
      const requestUrl = `threads/${selectedSpace?.token}/`;

      postDataApi(requestUrl, infoViewActionsContext, payload)
        .then((res: any) => {
          // infoViewActionsContext.showMessage(res.message);
          setLoading(false);
          form.resetFields();
          setAttachments([]);
          setQuery(null);
          console.log('res', res);
          if (res.data.slug) {
            if (onDataSaved) {
              onDataSaved(res.data);
            } else {
              router.push(`/thread/${res.data.slug}/`);
            }
          }
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    } else {
      const requestUrl = `threads/anonymous/create/`;

      postDataApi(requestUrl, infoViewActionsContext, payload)
        .then((res: any) => {
          infoViewActionsContext.showMessage(res.message);
          setLoading(false);

          if (onDataSaved) {
            onDataSaved(res.data);
          } else {
            router.push(`/thread/${res.data.slug}/`);
          }
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
          setLoading(false);
        });
    }
  };

  const getPayload = (values: Record<string, any>) => {
    console.log('getPayload', values);
    let payload: Record<string, any> = {
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
      const {content, ...rest} = values;
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

  const onQuerySubmit = (values: Record<string, any>) => {
    if (values.content || attachments?.length) {
      setLoading(true);
      const payload = getPayload(values);

      if (attachments?.length) {
        uploadAttachments(savePost, payload);
      } else {
        savePost(payload);
      }
    } else {
      const payload = getPayload(values);
      payload.content_type = POST_CONTENT_TYPE.VOICE;
      payload.post_type = 'ask';
      savePost(payload);
    }
  };

  const handleAttachmentChange = (file: any) => {
    const extension = getFileExtension(file.name)?.toLowerCase();
    if (
      AskAttachmentTypes &&
      !AskAttachmentTypes.includes(extension) &&
      (!file.type ||
        (!AskAttachmentTypes.includes(file.type) &&
          !AskAttachmentTypes.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({id: 'validation.fileTypeNotAllowed'}),
      );
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event: any, file: any) => {
    event.stopPropagation();
    setAttachments((prevState) =>
      prevState.filter((item) => item.uid !== file.uid),
    );
  };

  useImperativeHandle(ref, () => {
    return {
      setActivePilot(newPilot: any) {
        console.log('newPilot', newPilot);
      },
      askQuery(values: Record<string, any>) {
        onQuerySubmit(values);
      },
      resetContext() {
        setContext(null);
        setQuery(null);
        form.setFieldValue('content', null);
      },
      setContext(content: string, context: any) {
        if (content) {
          setQuery(content);
          form.setFieldValue('content', content);
          inputRef.current?.focus?.({preventScroll: true});
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
          <Text style={{marginRight: 5}}>{item.name}</Text>
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

  // console.log('AppQueryWindow activeOrg', activeOrg);

  return (
    <Fragment>
      <Form
        onFinish={onQuerySubmit}
        form={form}
        style={{maxWidth: '640px', width: '100%', margin: '0 auto'}}
      >
        <StyledContainer>
          <StyledMainContent>
            {context && (
              <ContextView context={context} onContextClose={onContextClose}/>
            )}

            <Item name="content">
              <StyledInput
                placeholder={formatMessage({id: 'common.askAnything'})}
                variant="borderless"
                autoSize={{minRows: 1, maxRows: 8}}
                onChange={(e) => setQuery(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    form.submit();
                  }
                }}
                ref={inputRef}
              />
            </Item>
          </StyledMainContent>

          <StyledBottomBar>
            {/* <Space align="center" size={4}>
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
                        title={
                          currentPrivacy?.label
                            ? formatMessage({ id: currentPrivacy.label })
                            : ''
                        }
                      >
                        <StyledIconButton type="text" shape="round">
                          {currentPrivacy?.icon}
                          {currentPrivacy?.label}
                        </StyledIconButton>
                      </Tooltip>
                    </Dropdown>
                  </PostPermissionPopover>
                </Fragment>
              )}
            </Space>*/}

            <Space size="small" align="center" style={{marginLeft: 'auto'}}>
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
                      <Badge
                        count={attachments?.length}
                        offset={[-5, 2]}
                        size="small"
                      >
                        <Button
                          type={attachments?.length ? 'primary' : 'default'}
                          shape="circle"
                          size="small"
                          icon={<MdOutlineAttachment fontSize={18}/>}
                        />
                      </Badge>
                    </Dropdown>
                  ) : (
                    <Button
                      type={attachments?.length ? 'primary' : 'default'}
                      shape="circle"
                      size="small"
                      icon={<MdOutlineAttachment fontSize={18}/>}
                    />
                  )}
                </Upload>
              )}

              <Button
                shape="circle"
                size="small"
                onClick={() => {
                  const payload = getPayload({content: ''});
                  payload.content_type = POST_CONTENT_TYPE.VOICE;
                  payload.post_type = 'ask';
                  savePost(payload);
                }}
                icon={<RiVoiceprintLine fontSize={18}/>}
              />

              {scheduleBtn ? (
                <SendButton
                  attachments={attachments}
                  query={query}
                  onSchedule={(values) =>
                    onQuerySubmit({...values, content: query})
                  }
                />
              ) : (
                (query || attachments?.length > 0) && (
                  <Button
                    type="primary"
                    ghost
                    shape="circle"
                    size="small"
                    htmlType="submit"
                    disabled={!query && !attachments?.length}
                    icon={<SendOutlined/>}
                  />
                )
              )}
            </Space>
          </StyledBottomBar>
        </StyledContainer>
      </Form>

      {loading && <AppLoader/>}
    </Fragment>
  );
};

AppQueryWindow.displayName = 'UserQuery';

export default AppQueryWindow;
