import {
  type ChangeEvent,
  Fragment,
  type KeyboardEvent,
  type MouseEvent,
  useEffect,
  useMemo,
  useState,
} from 'react';
import clsx from 'clsx';
import {
  Badge,
  Button,
  Dropdown,
  Form,
  Row,
  Space,
  Typography,
  Upload,
} from 'antd';
import {
  MdArrowForward,
  MdClose,
  MdDelete,
  MdOutlineAttachment,
} from 'react-icons/md';
import { BsArrowReturnLeft } from 'react-icons/bs';
import { uploadDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { AskAttachmentTypes } from '@unpod/constants';
import { POST_TYPE } from '@unpod/constants/AppEnums';
import AppLoader from '@unpod/components/common/AppLoader';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import {
  StyledBottomBar,
  StyledDivider,
  StyledInput,
  StyledOverlay,
  StyledParent,
  StyledParentContainer,
  StyledPilotContainer,
  StyledPilotRoot,
} from './index.styled';
import { useIntl } from 'react-intl';

const { Item, useForm } = Form;

type PilotInputWindowProps = {
  currentPost: any;
  replyParent: any;
  setReplyParent: (value: any) => void;
  sendJsonMessage: (value: any) => void;
};

const PilotInputWindow = ({
  currentPost,
  replyParent,
  setReplyParent,
  sendJsonMessage,
}: PilotInputWindowProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [focused, setFocused] = useState(false);
  const [newQuery, setNewQuery] = useState<string | null>(null);
  const [requestPilot, setRequestedPilot] = useState<string | null>(null);
  const [form] = useForm();
  const [attachments, setAttachments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const { formatMessage } = useIntl();

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
    }
  }, [currentPost]);

  useEffect(() => {
    if (replyParent?.thread_id) {
      setFocused(true);
    }
  }, [replyParent]);

  const uploadAttachments = (callbackFun: (data: any) => void, data: any) => {
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

  const submitQuestion = (data: any) => {
    const parentData: Record<string, any> = {};
    if (replyParent?.block_id) {
      parentData.parent_id = replyParent.block_id;
    }

    sendJsonMessage({
      event: 'block',
      pilot: requestPilot || '',
      data: {
        block: 'html',
        content_type: 'question',
        block_type: requestPilot ? 'question' : 'text_msg',
        data: data,
        ...parentData,
      },
    });

    setReplyParent(null);
    setNewQuery(null);
    setFocused(false);
    setLoading(false);
    form.resetFields();
  };

  const onQuerySubmit = (values: any = null) => {
    if (values && Object.keys(values).length > 0) {
      setLoading(true);
      const data = {
        content: values.content,
        knowledge_bases:
          currentPost?.knowledge_bases.map((kb: any) => kb.slug) || [],
      };

      if (attachments?.length) {
        uploadAttachments(submitQuestion, data);
      } else {
        submitQuestion(data);
      }
    }
  };

  const onFocused = () => {
    setFocused(true);
  };

  const onOverlayClick = () => {
    if (!replyParent?.block_id) setFocused(false);
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
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
    } else {
      setAttachments((prevState) => [...prevState, file]);
    }

    return false;
  };

  const onAttachmentRemove = (event: MouseEvent, file: any) => {
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
          <Typography.Text style={{ marginRight: 5 }}>
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

  const isEnabled = (newQuery?.length ?? 0) > 2;

  return (
    <Fragment>
      <StyledPilotRoot>
        <Form onFinish={onQuerySubmit} form={form}>
          <StyledPilotContainer
            onFocus={onFocused}
            onMouseDown={onFocused}
            className={clsx({ focused: focused })}
          >
            {replyParent && (
              <StyledParentContainer>
                <StyledParent>
                  <BsArrowReturnLeft fontSize={16} />
                  <Typography.Paragraph type="secondary" ellipsis>
                    {formatMessage(
                      { id: 'ask.replyingTo' },
                      {
                        name: replyParent.title
                          ? replyParent.title
                          : getStringFromHtml(replyParent?.data?.content),
                      },
                    )}
                  </Typography.Paragraph>

                  <Button
                    type="text"
                    icon={<MdClose fontSize={16} />}
                    size="small"
                    onClick={() => setReplyParent(null)}
                  />
                </StyledParent>
                <StyledDivider />
              </StyledParentContainer>
            )}

            <Item name="content">
              <StyledInput
                placeholder={formatMessage({ id: 'ask.askFollowup' })}
                variant="borderless"
                autoSize={{ minRows: 1, maxRows: 10 }}
                onPressEnter={(e: KeyboardEvent<HTMLTextAreaElement>) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    form.submit();
                  }
                }}
                value={newQuery ?? ''}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                  setNewQuery(e.target.value)
                }
              />
            </Item>

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
                          size="small"
                          icon={<MdOutlineAttachment fontSize={18} />}
                        />
                      </Badge>
                    </Dropdown>
                  ) : (
                    <Button
                      type={attachments?.length ? 'primary' : 'default'}
                      shape="circle"
                      size="small"
                      icon={<MdOutlineAttachment fontSize={18} />}
                    />
                  )}
                </Upload>

                <Button
                  type={isEnabled ? 'primary' : 'default'}
                  shape="circle"
                  size="small"
                  htmlType="submit"
                  icon={<MdArrowForward fontSize={18} />}
                />
              </Space>
            </StyledBottomBar>
          </StyledPilotContainer>
        </Form>
      </StyledPilotRoot>

      <StyledOverlay
        onClick={onOverlayClick}
        className={clsx({ focused: focused })}
      />

      {loading && <AppLoader />}
    </Fragment>
  );
};

export default PilotInputWindow;
