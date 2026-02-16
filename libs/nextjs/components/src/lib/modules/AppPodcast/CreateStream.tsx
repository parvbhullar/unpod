import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import {
  postDataApi,
  putDataApi,
  uploadDataApi,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { PERMISSION_TYPES } from '@unpod/constants';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { Dropdown, Form, Progress, Row, Space, Typography, Upload } from 'antd';
import {
  AppMiniWindowBody,
  AppMiniWindowFooter,
} from '../../common/AppMiniWindow';

import {
  StyledButton,
  StyledCoverWrapper,
  StyledDelContainer,
  StyledFormItem,
  StyledInput,
} from './index.styled';
import {
  MdClear,
  MdFormatColorText,
  MdOutlineImage,
  MdOutlineWorkspaces,
} from 'react-icons/md';
import { useParams, useRouter } from 'next/navigation';
import AppImage from '../../lib/next/AppImage';
import AppEditor from '../../third-party/AppEditor';
import PostPermissionPopover from '../../common/PermissionPopover/PostPermissionPopover';
import { POST_CONTENT_TYPE, POST_TYPE } from '@unpod/constants/AppEnums';
import _debounce from 'lodash/debounce';
import { getDraftData, saveDraftData } from '@unpod/helpers/DraftHelper';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import { useIntl } from 'react-intl';

const acceptTypes = '.png, .jpg, .jpeg';

const CreateStream = ({
  onSaved,
  currentSpace,
  currentPost,
  isEdit,
  setCreatingPost,
}) => {
  const router = useRouter();
  const [form] = Form.useForm();
  const { spaceSlug, postSlug } = useParams();
  const infoViewActionsContext = useInfoViewActionsContext();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = React.useState(null);
  const [content, setContent] = React.useState(null);
  const [privacyType, setPrivacyType] = useState('private');
  const [currentPrivacy, setCurrentPrivacy] = useState(null);
  const [spaceList, setSpaceList] = useState([]);
  const [selectedSpace, setSelectedSpace] = useState(null);
  const [coverPreviewUrl, setCoverPreviewUrl] = useState(null);
  const [coverImage, setCoverImage] = useState(null);
  const [coverUploadPercent, setCoverUploadPercent] = useState(0);
  const [userList, setUserList] = useState([]);
  const [visible, setSetVisible] = useState(false);
  const { formatMessage } = useIntl();
  const [dataFetched, setDataFetched] = useState(false);
  const debounceFn = useCallback(_debounce(saveDraftData, 2000), []);

  const [{ apiData }] = useGetDataApi(
    'spaces/',
    {},
    {},
    !spaceSlug && !postSlug,
  );

  useEffect(() => {
    if (dataFetched && !isEdit) {
      debounceFn(`stream-${postSlug || spaceSlug}`, {
        title: title,
        content: content,
        privacy: privacyType,
        users: userList,
      });
    }
  }, [
    title,
    content,
    privacyType,
    userList,
    spaceSlug,
    postSlug,
    dataFetched,
    isEdit,
  ]);

  useEffect(() => {
    if (!dataFetched) {
      if (!isEdit) {
        const draftData = getDraftData(`stream-${postSlug || spaceSlug}`);

        if (draftData) {
          setTitle(draftData.title);
          setContent(draftData.content);
          setPrivacyType(draftData.privacy);
          setUserList(draftData.users);

          form.setFieldsValue({
            title: draftData.title,
            content: draftData.content,
          });
        }
      }

      setTimeout(() => {
        setDataFetched(true);
      }, 1000);
    }
  }, [spaceSlug, postSlug, dataFetched, isEdit]);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType),
    );
  }, [privacyType]);

  useEffect(() => {
    if (currentSpace) {
      setSelectedSpace({
        key: currentSpace.token,
        label: currentSpace.name,
        token: currentSpace.token,
      });
    }
  }, [currentSpace]);

  useEffect(() => {
    if (currentPost) {
      setUserList(
        currentPost?.users?.map((item) => ({
          ...item,
          role_code: item.role,
        })),
      );

      const privacy = PERMISSION_TYPES.find(
        (item) => item.key === currentPost.privacy_type,
      );

      if (privacy?.key) setPrivacyType(privacy.key);
    } else if (currentSpace) {
      if (currentSpace?.users) {
        setUserList(
          currentSpace?.users.map((item) => ({
            ...item,
            role_code: item.role,
          })),
        );
      } else {
        setUserList([]);
      }

      if (currentSpace.privacy_type) {
        const privacy = PERMISSION_TYPES.find(
          (item) => item.key === currentSpace.privacy_type,
        );
        setPrivacyType(privacy.key);
      }
    }
  }, [currentSpace, currentPost]);

  useEffect(() => {
    if (apiData?.data) {
      setSpaceList(
        apiData.data.map((item) => ({
          key: item.token,
          label: item.name,
          token: item.token,
        })),
      );
    }
  }, [apiData?.data]);

  const handleCoverImageChange = (file) => {
    const extension = getFileExtension(file.name);
    if (
      acceptTypes &&
      !acceptTypes.includes(extension) &&
      (!file.type ||
        (!acceptTypes.includes(file.type) &&
          !acceptTypes?.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
    } else {
      setCoverPreviewUrl(window.URL.createObjectURL(file));
      setCoverImage(file);
    }

    return false;
  };

  const onRemoveCoverImage = () => {
    setCoverPreviewUrl(null);
    setCoverImage(null);
  };

  const savePodcast = (payload) => {
    if (currentPost?.slug && isEdit) {
      putDataApi(
        `threads/${currentPost?.slug}/action/`,
        infoViewActionsContext,
        {
          title: payload.title,
          content: payload.content,
        },
      )
        .then((response) => {
          infoViewActionsContext.showMessage(response.message);
          setCreatingPost(false);
          if (onSaved) onSaved(response);
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      let podcastCreateUrl = `threads/${selectedSpace?.token}/`;

      if (currentPost) {
        podcastCreateUrl = `threads/${
          currentPost?.parent_post_slug
            ? currentPost?.parent_post_slug
            : currentPost?.slug
        }/post/`;
      }
      setCreatingPost(true);
      postDataApi(
        podcastCreateUrl,
        infoViewActionsContext,
        {
          ...payload,
          post_type: POST_TYPE.POST,
          content_type: POST_CONTENT_TYPE.VIDEO_STREAM,
        },
        true,
      )
        .then((response) => {
          localStorage.removeItem(`stream-${postSlug || spaceSlug}`);
          infoViewActionsContext.showMessage(response.message);
          setCreatingPost(false);
          if (onSaved) onSaved(response);
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
          setCreatingPost(false);
        });
    }
  };

  const uploadCoverImage = (callbackFun) => {
    const formData = new FormData();
    formData.append('file', coverImage);
    formData.append('object_type', 'post');
    formData.append('media_relation', 'cover');

    uploadDataApi(
      `media/upload/`,
      infoViewActionsContext,
      formData,
      false,
      (progressEvent) => {
        setCoverUploadPercent(
          Math.round((progressEvent.loaded * 100) / progressEvent.total),
        );
      },
    )
      .then((response) => {
        callbackFun(response.data);
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const onSubmitSuccess = (postData) => {
    if (!selectedSpace) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.selectSpace' }),
      );
    } else {
      const payload = {
        ...postData,
        scheduled: false,
        //tags: ['Test', 'Demo'],
        privacy_type: privacyType,
        user_list: privacyType === 'shared' ? userList : [],
      };

      if (coverImage) {
        uploadCoverImage(({ media_id }) => {
          payload.cover_image = {
            media_id: media_id,
            file_name: coverImage.name,
          };
          savePodcast(payload);
        });
      } else {
        savePodcast(payload);
      }
    }
  };

  const onSpaceChange = (option) => {
    setSelectedSpace(spaceList.find((space) => space.key === option.key));
  };

  const onShareChange = (option) => {
    setPrivacyType(option.key);
    if (option.key === 'shared') {
      setOpen(true);
    }
  };

  const onTitleChange = (e) => {
    const newTitle = e.target.value;
    setTitle(newTitle);
  };

  return (
    <Form
      onFinish={onSubmitSuccess}
      initialValues={isEdit ? currentPost : {}}
      layout="vertical"
      form={form}
    >
      <AppMiniWindowBody>
        <StyledFormItem
          name="title"
          rules={[
            {
              required: true,
              message: formatMessage({ id: 'common.titleError' }),
            },
          ]}
        >
          <StyledInput
            placeholder={formatMessage({ id: 'form.title' })}
            variant="borderless"
            onChange={onTitleChange}
          />
        </StyledFormItem>

        {/*<Form.Item
          name="content"
          rules={[
            {
              required: true,
              message: 'Content is required',
            },
          ]}
        >
          <StyledMailModalTextArea
            theme='snow'
            placeholder="Content"
          />
        </Form.Item>*/}
        <AppEditor
          name="content"
          placeholder={formatMessage({ id: 'post.content' })}
          required
          visible={visible}
          value={isEdit ? currentPost.content : content}
          onChange={(content) => setContent(content)}
          isCoverImage={!!coverPreviewUrl}
        >
          {coverUploadPercent > 0 && coverUploadPercent < 100 ? (
            <Form.Item label={formatMessage({ id: 'post.coverImage' })}>
              <Progress percent={coverUploadPercent} width={70} />
            </Form.Item>
          ) : (
            !!coverPreviewUrl && (
              <Form.Item label={formatMessage({ id: 'post.coverImage' })}>
                <StyledCoverWrapper>
                  <AppImage
                    src={coverPreviewUrl}
                    alt="Cover Image"
                    layout="fill"
                    objectFit="cover"
                  />
                </StyledCoverWrapper>

                <StyledDelContainer>
                  <MdClear
                    fontSize={16}
                    onClick={onRemoveCoverImage}
                    className="remove-cover-handle"
                  />
                </StyledDelContainer>
              </Form.Item>
            )
          )}
        </AppEditor>
      </AppMiniWindowBody>

      <AppMiniWindowFooter>
        <Row justify="space-between" align="middle" wrap={false}>
          <Space size="large" wrap>
            {!spaceSlug && !postSlug && (
              <Dropdown
                menu={{
                  items: spaceList,
                  onClick: onSpaceChange,
                  selectedKeys: selectedSpace?.key,
                }}
                trigger={['click']}
                arrow
              >
                <Typography.Link>
                  <Space>
                    <MdOutlineWorkspaces fontSize={21} />

                    <span>
                      {selectedSpace?.label
                        ? selectedSpace.label.slice(0, 20).trim()
                        : formatMessage({ id: 'space.space' })}
                    </span>
                  </Space>
                </Typography.Link>
              </Dropdown>
            )}

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
              <Typography.Link>
                <Space>
                  {currentPrivacy?.icon}
                  <span>{formatMessage({ id: currentPrivacy?.label })}</span>
                </Space>
              </Typography.Link>
            </Dropdown>
          </Space>

          <Space size="large" align="center">
            <Typography.Link
              type={visible ? '' : 'secondary'}
              onClick={() => setSetVisible(!visible)}
              css={`
                display: inline-block;
                margin-bottom: 2px;
              `}
            >
              <MdFormatColorText fontSize={20} />
            </Typography.Link>

            <Upload
              name="file"
              accept={acceptTypes}
              maxCount={1}
              beforeUpload={handleCoverImageChange}
              multiple={false}
              showUploadList={false}
            >
              <Typography.Link>
                <MdOutlineImage fontSize={24} />
              </Typography.Link>
            </Upload>

            <StyledButton type="primary" htmlType="submit">
              {formatMessage({ id: 'common.startStreaming' })}
            </StyledButton>
          </Space>
        </Row>

        <PostPermissionPopover
          open={open}
          setOpen={setOpen}
          userList={userList}
          setUserList={setUserList}
        />
      </AppMiniWindowFooter>
      {/*{creatingPost && <AppLoader />}*/}
    </Form>
  );
};

CreateStream.propTypes = {
  onSaved: PropTypes.func,
  space: PropTypes.object,
};

export default CreateStream;
