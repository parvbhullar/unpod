import type {CSSProperties, MouseEvent} from 'react';
import {memo, useCallback, useEffect, useMemo, useState} from 'react';
import {
  StyledBottomBar,
  StyledCloseButton,
  StyledDivider,
  StyledIconWrapper,
  StyledInput,
  StyledMainContent,
  StyledOverlay,
  StyledParent,
  StyledParentContainer,
  StyledPilotContainer,
  StyledPilotRoot,
  StyledSelect,
  StyledTopBar,
  StylesPilotLogo,
} from './index.styled';
import {Badge, Button, Col, Dropdown, Form, Row, Select, Space, Typography, Upload,} from 'antd';
import {MdArrowForward, MdClose, MdDelete, MdOutlineAttachment, MdOutlineWorkspaces,} from 'react-icons/md';
import clsx from 'clsx';

import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import {BsArrowReturnLeft, BsFillFileEarmarkPersonFill} from 'react-icons/bs';
import {POST_TYPE} from '@unpod/constants/AppEnums';
import _debounce from 'lodash/debounce';
import {getDraftData, saveDraftData} from '@unpod/helpers/DraftHelper';
import {useRouter} from 'next/navigation';
import {getDataApi, uploadDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {AskAttachmentTypes} from '@unpod/constants';
import {getFileExtension} from '@unpod/helpers/FileHelper';
import AppLoader from '../../common/AppLoader';
import AppImage from '../../next/AppImage';
import AppSuperbookInputs from '../../common/AppSuperbookInputBlock/AppSuperbookInputs';
import {getDateObject} from '@unpod/helpers/DateHelper';
import {getJsonString} from '@unpod/helpers/StringHelper';
import {useIntl} from 'react-intl';
import type {Pilot, Spaces} from '@unpod/constants/types';

/*const AppEditorInput = dynamic(import('../AppEditor/AppEditorInput'));*/

const defaultPilot = {
  handle: 'superpilot',
  name: '@Superpilot',
};

const {Item, useForm} = Form;

type KnowledgeBaseItem = Spaces;

type InputSchemaItem = {
  name: string;
  type: string;
  defaultValue?: any;
  [key: string]: any;
};

type InputFormBlock = {
  input_schema?: InputSchemaItem[];
  block_type?: string;
  [key: string]: any;
};

type ReplyParent = {
  thread_id?: string;
  block_id?: string;
  title?: string;
  data?: { content?: string };
  [key: string]: any;
};

type AttachmentFile = File & { uid?: string; name: string };

type CurrentPost = {
  slug?: string;
  related_data?: { pilot?: string; knowledge_bases?: string[] };
  post_type?: string;
  [key: string]: any;
};

type AppPostQuestionWindowProps = {
  currentPost?: CurrentPost | null;
  replyParent?: ReplyParent | null;
  setReplyParent?: (value: ReplyParent | null) => void;
  sendJsonMessage?: (payload: any) => void;
  rootStyle?: CSSProperties;
  overlayStyle?: CSSProperties;
  placeholder?: string;
};

const AppPostQuestionWindow = ({
                                 currentPost,
                                 replyParent,
                                 setReplyParent,
                                 sendJsonMessage,
                                 rootStyle,
                                 overlayStyle,
                                 placeholder = 'Ask me to do anything...',
                               }: AppPostQuestionWindowProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter() as {
    events?: {
      on: (event: string, cb: () => void) => void;
      off: (event: string, cb: () => void) => void;
    };
  };
  const {isAuthenticated} = useAuthContext();
  const [focused, setFocused] = useState(false);
  const [newQuery, setNewQuery] = useState<string | null>(null);
  const [requestPilot, setRequestedPilot] = useState<string | null>(null);
  const [pilot, setPilot] = useState<Pilot | null>(defaultPilot);
  const [form] = useForm();
  const {formatMessage} = useIntl();

  const [dataFetched, setDataFetched] = useState(false);
  const [pilots, setPilots] = useState<Pilot[]>([]);
  const [kbList, setKbList] = useState<KnowledgeBaseItem[]>([]);
  const [knBasesData, setKnowledgeBasesData] = useState<KnowledgeBaseItem[]>(
    [],
  );
  const [knowledgeBases, setKnowledgeBases] = useState<string[]>([]);
  const [attachments, setAttachments] = useState<AttachmentFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputFormBlock, setInputFormBlock] = useState<InputFormBlock | null>(
    null,
  );

  const debounceFn = useCallback(_debounce(saveDraftData, 3000), []);

  useEffect(() => {
    const routeChangeStart = () => {
      setDataFetched(false);
    };
    if (router.events?.on) {
      router.events.on('routeChangeStart', routeChangeStart);
      return () => {
        router.events?.off('routeChangeStart', routeChangeStart);
      };
    }
    return;
  }, [router]);

  useEffect(() => {
    getDataApi('core/pilots/public/', infoViewActionsContext, {
      case: 'all',
    })
      .then((response: any) => {
        setPilots(response.data);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });

    if (isAuthenticated) {
      getDataApi('core/knowledgebase/', infoViewActionsContext)
        .then((response: any) => {
          setKnowledgeBasesData(response.data);
        })
        .catch((error: any) => {
          infoViewActionsContext.showError(error.message);
        });
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (dataFetched && currentPost?.slug) {
      debounceFn(`ask-${currentPost?.slug}`, {content: newQuery});
    }
  }, [newQuery, requestPilot, dataFetched, currentPost?.slug]);

  useEffect(() => {
    if (!dataFetched && currentPost?.slug) {
      const draftData = getDraftData<{ content?: string }>(
        `ask-${currentPost?.slug}`,
      );

      if (draftData) {
        setNewQuery(draftData.content || null);
      }

      setTimeout(() => {
        setDataFetched(true);
      }, 1000);
    }
  }, [currentPost?.slug, dataFetched]);

  useEffect(() => {
    if (currentPost?.slug) {
      setFocused(false);
      const pilot =
        currentPost?.related_data?.pilot ||
        (currentPost.post_type === POST_TYPE.TASK ||
        currentPost.post_type === POST_TYPE.ASK
          ? 'superpilot'
          : null);
      setRequestedPilot(pilot);

      setKnowledgeBases(currentPost?.related_data?.knowledge_bases || []);
    }
  }, [currentPost]);

  useEffect(() => {
    if (requestPilot) {
      const pilot = pilots?.find((item) => item.handle === requestPilot);

      if (pilot) {
        if (pilot.allow_user_to_change) {
          setKbList(pilot.kb_list || []);
        } else {
          setKbList([]);
        }
      } else {
        setKbList(knBasesData);
      }

      if (requestPilot !== defaultPilot.handle) {
        getDataApi(
          `core/pilots/${requestPilot}/blocks/`,
          infoViewActionsContext,
        )
          .then((response: any) => {
            setLoading(false);

            setInputFormBlock(
              response.data.find(
                (block: InputFormBlock) => block.block_type === 'input_form',
              ) || null,
            );
          })
          .catch((error: any) => {
            setLoading(false);

            if (error.message !== 'Pilot Not Found') {
              infoViewActionsContext.showError(error.message);
            }
          });
      } else {
        setInputFormBlock(null);
      }
    }
  }, [requestPilot, pilots, knBasesData]);

  useEffect(() => {
    if (inputFormBlock?.input_schema) {
      const initialData: Record<string, any> = {};
      for (const item of inputFormBlock.input_schema) {
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
    }
  }, [inputFormBlock?.input_schema]);

  useEffect(() => {
    if (replyParent?.thread_id) {
      setFocused(true);
    }
  }, [replyParent]);

  const uploadAttachments = (
    callbackFun: (payload: Record<string, any>) => void,
    data: Record<string, any>,
  ) => {
    const formData = new FormData();
    formData.append('object_type', 'post');
    attachments.forEach((file) => {
      formData.append('files', file);
    });

    uploadDataApi(`media/upload-multiple/`, infoViewActionsContext, formData)
      .then((res: any) => {
        data.files = res.data;
        setAttachments([]);
        callbackFun(data);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const submitQuestion = (data: Record<string, any>) => {
    const parentData: Record<string, any> = {};
    if (replyParent?.block_id) {
      parentData.parent_id = replyParent.block_id;
    }

    sendJsonMessage?.({
      event: 'block',
      pilot: requestPilot || '',
      data: {
        block: 'html',
        block_type: requestPilot ? 'question' : 'text_msg',
        data: data,
        ...parentData,
      },
    });

    setReplyParent?.(null);
    setNewQuery(null);
    setFocused(false);
    setLoading(false);
  };

  const onQuerySubmit = (values: Record<string, any> | null = null) => {
    // const question = content || newQuery;

    if (values && Object.keys(values).length > 0) {
      setLoading(true);
      const data = {
        content: Object.keys(values).length > 0 ? JSON.stringify(values) : null,
        knowledge_bases: requestPilot ? knowledgeBases : [],
      };

      if (attachments?.length) {
        uploadAttachments(submitQuestion, data);
      } else {
        submitQuestion(data);
      }
    } else {
      setTimeout(() => {
        setNewQuery(null);
      }, 100);
    }
  };

  const onFocused = () => {
    setFocused(true);
  };

  const onOverlayClick = () => {
    if (!replyParent?.block_id) setFocused(false);
  };

  const onChangePilot = (newPilot: string) => {
    setKnowledgeBases([]);
    setRequestedPilot(newPilot);
    setPilot(pilots?.find((item) => item.handle === newPilot) || null);
  };

  const onClosePilot = () => {
    setPilot(null);
    setKnowledgeBases([]);
    setRequestedPilot(null);
    setInputFormBlock(null);
  };

  const handleAttachmentChange = (file: AttachmentFile) => {
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

  const onAttachmentRemove = (event: MouseEvent, file: AttachmentFile) => {
    event.stopPropagation();
    setAttachments((prevState) =>
      prevState.filter(
        (item) => (item.uid ?? item.name) !== (file.uid ?? file.name),
      ),
    );
  };

  const attachmentsList = useMemo(() => {
    return attachments.map((item) => ({
      key: item.uid ?? item.name,
      label: (
        <Row justify="space-between" align="middle">
          <Typography.Text style={{marginRight: 5}}>
            {item.name}
          </Typography.Text>
          <MdDelete
            fontSize={18}
            onClick={(event) => onAttachmentRemove(event, item)}
          />
        </Row>
      ),
    }));
  }, [attachments]);

  return (
    <>
      <StyledPilotRoot style={rootStyle}>
        <Form onFinish={onQuerySubmit} form={form}>
          <StyledTopBar>
            <Space size="small" align="center">
              {pilot?.logo ? (
                <StylesPilotLogo>
                  <AppImage
                    src={`${pilot.logo}?tr=w-18,h-20`}
                    alt="logo"
                    height={20}
                    width={18}
                    layout="fill"
                    objectFit="cover"
                  />
                </StylesPilotLogo>
              ) : (
                <StyledIconWrapper>
                  <BsFillFileEarmarkPersonFill fontSize={18}/>
                </StyledIconWrapper>
              )}

              <StyledSelect
                variant="borderless"
                size="small"
                placeholder={formatMessage({id: 'common.superPilot'})}
                value={requestPilot || undefined}
                onChange={(value) => onChangePilot(value as string)}
                style={{
                  minWidth: 120,
                  width: 'max-content',
                }}
              >
                <Select.Option value="superpilot">@SuperPilot</Select.Option>

                {pilots.map(
                  (item) =>
                    item.privacy_type === 'public' &&
                    item.state === 'published' && (
                      <Select.Option key={item.slug} value={item.handle}>
                        {item.name}
                      </Select.Option>
                    ),
                )}
              </StyledSelect>

              {requestPilot && (
                <StyledCloseButton onClick={onClosePilot}>
                  <MdClose/>
                </StyledCloseButton>
              )}
            </Space>

            {requestPilot === 'superpilot' && isAuthenticated && (
              <Space size="small" align="center">
                <MdOutlineWorkspaces fontSize={16}/>

                <Select
                  variant="borderless"
                  size="small"
                  style={{
                    minWidth: 160,
                    width: 'max-content',
                  }}
                  mode="multiple"
                  maxTagCount={1}
                  placeholder={formatMessage({id: 'knowledgeBase.pageTitle'})}
                  disabled={kbList?.length === 0}
                  value={knowledgeBases}
                  onChange={setKnowledgeBases}
                >
                  {kbList?.map((item) => (
                    <Select.Option key={item.slug} value={item.slug}>
                      {item.name}
                    </Select.Option>
                  ))}
                </Select>
              </Space>
            )}
          </StyledTopBar>

          <StyledPilotContainer
            onFocus={onFocused}
            onMouseDown={onFocused}
            // onBlur={onBlurred}
            className={clsx({focused: focused})}
          >
            {replyParent && (
              <StyledParentContainer>
                <StyledParent>
                  <BsArrowReturnLeft fontSize={16}/>
                  <Typography.Paragraph type="secondary" ellipsis>
                    Replying to{' '}
                    {replyParent.title
                      ? replyParent.title
                      : getStringFromHtml(replyParent?.data?.content)}
                  </Typography.Paragraph>

                  <Button
                    type="text"
                    icon={<MdClose fontSize={16}/>}
                    size="small"
                    onClick={() => setReplyParent?.(null)}
                  />
                </StyledParent>
                <StyledDivider/>
              </StyledParentContainer>
            )}

            <StyledMainContent>
              {inputFormBlock && (
                <Row gutter={16}>
                  {(inputFormBlock?.input_schema || []).map((item, index) =>
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
              )}

              <Item name="content">
                <StyledInput
                  placeholder={
                    (inputFormBlock?.input_schema || []).length > 0
                      ? formatMessage({id: 'superbook.instructionsOptional'})
                      : formatMessage({id: 'superbook.askMeAnything'})
                  }
                  maxLength={200}
                  variant="borderless"
                  autoSize={{minRows: 2, maxRows: 3}}
                  size="large"
                />
              </Item>
            </StyledMainContent>

            {/*<AppEditorInput
              placeholder={placeholder}
              toolbarId="post-reply"
              value={newQuery}
              onChange={onEditorChange}
              onKeyDown={(event) => {
                if (event.shiftKey) {
                  shiftKey.current = true;
                }

                if (!shiftKey.current && event.key === 'Enter') {
                  onQuerySubmit(event.target.innerHTML);
                }
              }}
              onKeyUp={(event) => {
                if (!event.shiftKey) {
                  shiftKey.current = false;
                }
              }}
            />*/}

            <StyledBottomBar>
              <Space size="small" align="center">
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
                        size="small"
                        offset={[-5, 2]}
                      >
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
                    {formatMessage({id: 'common.run'})}{' '}
                    <MdArrowForward fontSize={18}/>
                  </Space>
                </Button>

                {/*<Button
                  type={isEnabled ? 'primary' : 'default'}
                  shape="circle"
                  size="small"
                  icon={<MdArrowForward fontSize={18} />}
                  onClick={() => onQuerySubmit()}
                />*/}
              </Space>
            </StyledBottomBar>
          </StyledPilotContainer>
        </Form>
      </StyledPilotRoot>

      <StyledOverlay
        onClick={onOverlayClick}
        className={clsx({focused: focused})}
        style={focused ? overlayStyle : undefined}
      />
      {loading && <AppLoader/>}
    </>
  );
};

export default memo(AppPostQuestionWindow);
