import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import {postDataApi, putDataApi, uploadDataApi, useInfoViewActionsContext,} from '@unpod/providers';
import {PERMISSION_TYPES} from '@unpod/constants';
import {ACCESS_ROLE, POST_CONTENT_TYPE, POST_TYPE,} from '@unpod/constants/AppEnums';
import CommonFields from './CommonFields';
import {StyledContainer, StyledPostContainer} from './index.styled';

const ANONYMOUS_TITLE = 'Write Title';

const WriteThread = ({post, tagsData, currentSpace, setThreadType, onDataSaved}) => {
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
    let payload = {
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
      content_type: POST_CONTENT_TYPE.TEXT,
      tags: tags,
      files: [],
    };

    if (coverImage) {
      uploadCoverImage(({media_id}) => {
        payload.cover_image = {
          media_id: media_id,
          file_name: coverImage.name,
        };

        saveData(payload);
      });
    } else {
      saveData(payload);
    }
  };

  const isSubEnabled = queryTitle && queryTitle.length > 2;

  return (
    <StyledContainer>
      {/*<div>{`Draft under ${currentSpace.name}`}</div>*/}

      <StyledPostContainer>
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
          setThreadType={setThreadType}
        />
      </StyledPostContainer>
    </StyledContainer>
  );
};

const {func, object} = PropTypes;

WriteThread.propTypes = {
  post: object,
  tagsData: object,
  currentSpace: object,
  onDataSaved: func,
};

export default WriteThread;
