import React, { useCallback, useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import {
  getDataApi,
  postDataApi,
  uploadDataApi,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { PERMISSION_TYPES } from '@unpod/constants';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import {
  Button,
  Dropdown,
  Form,
  Progress,
  Row,
  Space,
  Typography,
  Upload,
} from 'antd';
import * as UpChunk from '@mux/upchunk';
import {
  AppMiniWindowBody,
  AppMiniWindowFooter,
} from '../../common/AppMiniWindow';
import {
  StyledButton,
  StyledCoverWrapper,
  StyledDelContainer,
  StyledDragger,
  StyledFormItem,
  StyledInput,
} from './index.styled';
import {
  MdArrowUpward,
  MdClear,
  MdFormatColorText,
  MdOutlineImage,
  MdOutlineWorkspaces,
} from 'react-icons/md';
import { useParams, useRouter } from 'next/navigation';
import AppImage from '../../next/AppImage';
import AppEditor from '../../third-party/AppEditor';
import PostPermissionPopover from '../../common/PermissionPopover/PostPermissionPopover';
import {
  ACCESS_ROLE,
  POST_CONTENT_TYPE,
  POST_TYPE,
} from '@unpod/constants/AppEnums';
import _debounce from 'lodash/debounce';
import { getDraftData, saveDraftData } from '@unpod/helpers/DraftHelper';
import { useIntl } from 'react-intl';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';

const acceptTypes = '.png, .jpg, .jpeg';
const acceptMediaTypes = 'audio/*,video/*';

const UploadPodcast = ({
  onSaved,
  currentSpace,
  currentPost,
  setCreatingPost,
  isEdit,
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
  const [mediaList, setMediaList] = useState([]);
  const [media, setMedia] = useState(null);
  const [mediaUploadPercent, setMediaUploadPercent] = useState(0);
  const [userList, setUserList] = useState([]);
  const [visible, setSetVisible] = useState(false);
  const uploadedMediaRef = useRef(null);
  const { formatMessage } = useIntl();

  const [dataFetched, setDataFetched] = useState(false);
  const debounceFn = useCallback(_debounce(saveDraftData, 2000), []);

  const [{ apiData }] = useGetDataApi(
    'spaces/',
    {},
    { case: 'all' },
    !spaceSlug && !postSlug,
  );

  useEffect(() => {
    if (dataFetched && !isEdit) {
      debounceFn(`upload-podcast-${postSlug || spaceSlug}`, {
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
        const draftData = getDraftData(
          `upload-podcast-${postSlug || spaceSlug}`,
        );

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
    if (media) {
      window.onbeforeunload = function () {
        return true;
      };
    }

    return () => {
      window.onbeforeunload = null;
    };
  }, [media]);

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

  const handleUploadMediaChange = (file) => {
    const extension = getFileExtension(file.name);
    if (
      acceptMediaTypes &&
      !acceptMediaTypes.includes(extension) &&
      (!file.type ||
        (!acceptMediaTypes.includes(file.type) &&
          !acceptMediaTypes?.includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(
        formatMessage({ id: 'validation.fileTypeNotAllowed' }),
      );
    } else {
      setMediaList([file]);
      setMedia(file);
    }

    return false;
  };

  const onRemoveMedia = () => {
    setMedia(null);
    setMediaList([]);
  };

  const savePodcast = (payload) => {
    let podcastCreateUrl = `threads/${selectedSpace?.token}/`;

    if (currentPost) {
      podcastCreateUrl = `threads/${
        currentPost?.parent_post_slug
          ? currentPost?.parent_post_slug
          : currentPost?.slug
      }/post/`;
    }
    setCreatingPost(true);
    postDataApi(podcastCreateUrl, infoViewActionsContext, payload, true)
      .then((response) => {
        localStorage.removeItem(`upload-podcast-${postSlug || spaceSlug}`);
        setCreatingPost(false);
        infoViewActionsContext.showMessage(response.message);
        if (onSaved) onSaved(response);
      })
      .catch((response) => {
        setCreatingPost(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  const uploadMuxMedia = (callbackFun) => {
    setCreatingPost(true);
    if (uploadedMediaRef.current) {
      callbackFun(uploadedMediaRef.current.id);
      return;
    }
    getDataApi(`media/mux/get-upload-url/`, infoViewActionsContext, {}, true)
      .then((response) => {
        const upload = UpChunk.createUpload({
          endpoint: response.data.url,
          file: media,
          chunkSize: 5120, // Uploads the file in ~5mb chunks
        });

        upload.on('error', (error) => {
          setCreatingPost(false);
          infoViewActionsContext.showError(error.detail);
        });

        upload.on('progress', (progress) => {
          setMediaUploadPercent(Math.round(progress.detail));
        });

        upload.on('success', () => {
          uploadedMediaRef.current = response.data;
          callbackFun(response.data.id);
          setCreatingPost(false);
        });
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
        setCreatingPost(false);
      });
  };

  const uploadCoverImage = (callbackFun) => {
    const formData = new FormData();
    formData.append('file', coverImage);
    formData.append('object_type', 'post');
    formData.append('media_relation', 'cover');

    setCreatingPost(true);
    uploadDataApi(
      `media/upload/`,
      infoViewActionsContext,
      formData,
      true,
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
        setCreatingPost(false);
        infoViewActionsContext.showError(response.message);
      });
  };

  const onSubmitSuccess = (postData) => {
    if (!selectedSpace) {
      infoViewActionsContext.showError(formatMessage({id:'validation.selectSpace'}));
    } else {
      setCreatingPost(true);
      uploadMuxMedia((uploadId) => {
        const payload = {
          ...postData,
          post_type: POST_TYPE.POST,
          content_type: POST_CONTENT_TYPE.VIDEO,
          scheduled: false,
          tags: ['Test', 'Demo'],
          privacy_type: privacyType,
          user_list:
            privacyType === 'shared'
              ? userList.filter((user) => user.role_code !== ACCESS_ROLE.OWNER)
              : [],
          media: {
            upload_id: uploadId,
            file_name: media.name,
            size: media.size,
          },
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
      });
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
    <Form onFinish={onSubmitSuccess} layout="vertical" form={form}>
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

        <AppEditor
          name="content"
          placeholder={formatMessage({ id: 'post.content' })}
          visible={visible}
          value={isEdit ? currentPost.content : content}
          onChange={(newValue) => setContent(newValue)}
          isCoverImage={!!coverPreviewUrl}
        >
          <Form.Item
            label={formatMessage({ id: 'common.uploadVideoAudio' })}
            name="media"
            rules={[
              {
                required: true,
                message: formatMessage({ id: 'validation.chooseFile' }),
              },
            ]}
          >
            {mediaUploadPercent > 0 ? (
              <div>
                <Progress
                  percent={mediaUploadPercent}
                  css={`
                    margin-bottom: 8px;
                  `}
                />
              </div>
            ) : (
              <StyledDragger
                name="media"
                accept={acceptMediaTypes}
                maxCount={1}
                beforeUpload={handleUploadMediaChange}
                onRemove={onRemoveMedia}
                multiple={false}
                fileList={mediaList}
              >
                <Space direction="vertical" size={4}>
                  <Button
                    shape="circle"
                    icon={<MdArrowUpward fontSize={21} />}
                    css={`
                      margin-bottom: 8px;
                    `}
                  />

                  <Typography.Text>
                    {formatMessage({ id: 'post.dragMediaToUpload' })}
                  </Typography.Text>
                </Space>
              </StyledDragger>
            )}
          </Form.Item>

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

            <StyledButton type="primary" shape="round" htmlType="submit">
              Post
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
    </Form>
  );
};

UploadPodcast.propTypes = {
  onSaved: PropTypes.func,
  currentSpace: PropTypes.object,
  currentPost: PropTypes.object,
};

export default UploadPodcast;
