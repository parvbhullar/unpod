import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { Button, Modal, Progress, Space, Typography } from 'antd';
import { MdArrowUpward, MdEdit, MdVideoLibrary } from 'react-icons/md';
import { RiEyeLine } from 'react-icons/ri';
import * as UpChunk from '@mux/upchunk';
import AppMediaPlayer from '@unpod/components/common/AppMediaPlayer';
import {
  getDataApi,
  postDataApi,
  putDataApi,
  uploadDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { PERMISSION_TYPES } from '@unpod/constants';
import {
  ACCESS_ROLE,
  POST_CONTENT_TYPE,
  POST_TYPE,
} from '@unpod/constants/AppEnums';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import CommonFields from './CommonFields';
import {
  StyledContainer,
  StyledDragger,
  StyledIconWrapper,
  StyledMediaList,
  StyledMediaWrapper,
  StyledPostContainer,
} from './index.styled';

const ANONYMOUS_TITLE = 'Upload Title';
const acceptMediaTypes = 'audio/*,video/*';

const { Text, Title } = Typography;

const UploadThread = ({ post, tagsData, currentSpace, onDataSaved }) => {
  const infoViewActionsContext = useInfoViewActionsContext();

  const [queryTitle, setQueryTitle] = useState(null);
  const [content, setContent] = useState('');
  const [tags, setTags] = useState([]);
  const [userList, setUserList] = useState([]);
  const [privacyType, setPrivacyType] = useState('public');
  const [currentPrivacy, setCurrentPrivacy] = useState(null);

  const [coverUploadPercent, setCoverUploadPercent] = useState(0);
  const [coverPreviewUrl, setCoverPreviewUrl] = useState(null);
  const [coverImage, setCoverImage] = useState(null);

  const [editMedia, setEditMedia] = useState(false);
  const [preview, setPreview] = useState(false);
  const [media, setMedia] = useState(null);
  const [mediaUploadPercent, setMediaUploadPercent] = useState(0);
  const uploadedMediaRef = useRef(null);

  useEffect(() => {
    if (post) {
      setQueryTitle(post.title === ANONYMOUS_TITLE ? '' : post.title);
      setContent(post.content);
      setTags(post.tags);
      setPrivacyType(post.privacy_type);

      if (post?.cover_image)
        setCoverPreviewUrl(`${post.cover_image.url}?tr=w-960,h-540`);

      if (post.users) {
        setUserList(
          post.users.map((item) => ({
            ...item,
            role_code: item.role,
          }))
        );
      }
    } else {
      setQueryTitle('');
      setContent('');
      setTags([]);
      setPrivacyType('public');
      setCoverPreviewUrl(null);
      setCoverImage(null);

      if (currentSpace) {
        if (currentSpace.users) {
          setUserList(
            currentSpace?.users.map((item) => ({
              ...item,
              role_code: item.role,
            }))
          );
        } else {
          setUserList([]);
        }

        if (currentSpace.privacy_type) {
          const privacy = PERMISSION_TYPES.find(
            (item) => item.key === currentSpace.privacy_type
          );
          setPrivacyType(privacy.key);
        }
      }
    }
  }, [post, currentSpace]);

  useEffect(() => {
    setCurrentPrivacy(
      PERMISSION_TYPES.find((item) => item.key === privacyType)
    );
  }, [privacyType]);

  const saveData = (payload) => {
    if (post?.slug) {
      putDataApi(
        `threads/${post.slug}/action/`,
        infoViewActionsContext,
        payload
      )
        .then((response) => {
          infoViewActionsContext.showMessage(response.message);
          onDataSaved(response.data);
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
        });
    } else {
      const requestUrl = `threads/${currentSpace?.token}/`;

      postDataApi(requestUrl, infoViewActionsContext, payload, true)
        .then((response) => {
          infoViewActionsContext.showMessage(response.message);
          onDataSaved(response.data);
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
        });
    }
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
      infoViewActionsContext.showError(`File type is now allowed`);
    } else {
      setMedia(file);
    }

    return false;
  };

  const onRemoveMedia = () => {
    setMedia(null);
  };

  const uploadMuxMedia = (callbackFun) => {
    if (uploadedMediaRef.current) {
      callbackFun(uploadedMediaRef.current.id);
    } else {
      getDataApi(`media/mux/get-upload-url/`, infoViewActionsContext, {}, true)
        .then((response) => {
          const upload = UpChunk.createUpload({
            endpoint: response.data.url,
            file: media,
            chunkSize: 5120, // Uploads the file in ~5mb chunks
          });

          upload.on('error', (error) => {
            infoViewActionsContext.showError(error.detail);
          });

          upload.on('progress', (progress) => {
            setMediaUploadPercent(Math.round(progress.detail));
          });

          upload.on('success', () => {
            uploadedMediaRef.current = response.data;
            callbackFun(response.data.id);
          });
        })
        .catch((response) => {
          infoViewActionsContext.showError(response.message);
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
          Math.round((progressEvent.loaded * 100) / progressEvent.total)
        );
      }
    )
      .then((response) => {
        callbackFun(response.data);
      })
      .catch((response) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const submitRequest = (postStatus) => {
    const payload = {
      title: queryTitle || ANONYMOUS_TITLE,
      content: content || '',
      post_status: postStatus || 'draft',
      scheduled: false,
      privacy_type: privacyType,
      user_list:
        privacyType === 'shared'
          ? userList.filter((user) => user.role_code !== ACCESS_ROLE.OWNER)
          : [],
      post_type: POST_TYPE.POST,
      content_type: POST_CONTENT_TYPE.VIDEO,
      tags: tags,
      files: [],
    };

    if (media) {
      uploadMuxMedia((uploadId) => {
        payload.media = {
          upload_id: uploadId,
          file_name: media.name,
          size: media.size,
        };

        if (coverImage) {
          uploadCoverImage(({ media_id }) => {
            payload.cover_image = {
              media_id: media_id,
              file_name: coverImage.name,
            };
            saveData(payload);
          });
        } else {
          saveData(payload);
        }
      });
    } else {
      if (coverImage) {
        uploadCoverImage(({ media_id }) => {
          payload.cover_image = {
            media_id: media_id,
            file_name: coverImage.name,
          };
          saveData(payload);
        });
      } else {
        saveData(payload);
      }
    }
  };

  const isSubEnabled =
    queryTitle && queryTitle.length > 2 && (media || post?.media);

  return (
    <StyledContainer>
      {/*<div>{`Draft under ${currentSpace.name}`}</div>*/}

      <StyledPostContainer>
        {!media && post?.media && (
          <StyledMediaList>
            <Space size={12}>
              <MdVideoLibrary fontSize={16} />

              <Text>{post.media.name}</Text>
            </Space>

            {post?.post_status === 'draft' && (
              <Space size={12}>
                <StyledIconWrapper onClick={() => setPreview(true)}>
                  <RiEyeLine fontSize={16} />
                </StyledIconWrapper>

                <StyledIconWrapper onClick={() => setEditMedia(!editMedia)}>
                  <MdEdit fontSize={16} />
                </StyledIconWrapper>
              </Space>
            )}
          </StyledMediaList>
        )}

        {(editMedia || !post?.media) &&
          (mediaUploadPercent > 0 ? (
            <StyledMediaWrapper>
              <Title level={4} type="secondary" className="mb-0">
                Upload Media
              </Title>
              <Progress percent={mediaUploadPercent} />
            </StyledMediaWrapper>
          ) : (
            <StyledMediaWrapper>
              <StyledDragger
                name="media"
                accept={acceptMediaTypes}
                maxCount={1}
                beforeUpload={handleUploadMediaChange}
                onRemove={onRemoveMedia}
                multiple={false}
                fileList={media ? [media] : []}
              >
                <Space direction="vertical" size={4}>
                  <Button
                    shape="circle"
                    icon={<MdArrowUpward fontSize={21} />}
                    css={`
                      margin-bottom: 8px;
                    `}
                  />

                  <Text>Drag your audio/video files to upload</Text>
                </Space>
              </StyledDragger>
            </StyledMediaWrapper>
          ))}

        <CommonFields
          queryTitle={queryTitle}
          setQueryTitle={setQueryTitle}
          content={content}
          setContent={setContent}
          tags={tags}
          setTags={setTags}
          tagsData={tagsData}
          currentPrivacy={currentPrivacy}
          setPrivacyType={setPrivacyType}
          userList={userList}
          setUserList={setUserList}
          coverImage={coverImage}
          setCoverImage={setCoverImage}
          coverPreviewUrl={coverPreviewUrl}
          setCoverPreviewUrl={setCoverPreviewUrl}
          coverUploadPercent={coverUploadPercent}
          isSubEnabled={isSubEnabled}
          submitRequest={submitRequest}
        />
      </StyledPostContainer>

      {post && (
        <Modal
          title={post.title}
          open={preview}
          footer={null}
          width={960}
          onCancel={() => setPreview(false)}
          destroyOnHidden
        >
          <AppMediaPlayer
            title={post.title}
            media={post.media}
            poster={
              post.cover_image && `${post.cover_image.url}?tr=w-960,h-540`
            }
          />
        </Modal>
      )}
    </StyledContainer>
  );
};

const { func, object } = PropTypes;

UploadThread.propTypes = {
  post: object,
  tagsData: object,
  currentSpace: object,
  onDataSaved: func,
};

export default UploadThread;
