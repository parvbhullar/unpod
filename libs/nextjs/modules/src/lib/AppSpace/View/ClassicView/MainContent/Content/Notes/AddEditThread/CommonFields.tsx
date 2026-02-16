import React, { Fragment, useState } from 'react';
import PropTypes from 'prop-types';
import {
  Badge,
  Button,
  Dropdown,
  Progress,
  Select,
  Space,
  Typography,
  Upload,
} from 'antd';
import { MdClear, MdOutlineImage } from 'react-icons/md';
import AppImage from '@unpod/components/next/AppImage';
import AppMarkdownEditor from '@unpod/components/third-party/AppMarkdownEditor';
import PostPermissionPopover from '@unpod/components/common/PermissionPopover/PostPermissionPopover';
import { PERMISSION_TYPES } from '@unpod/constants';
import { getFileExtension } from '@unpod/helpers/FileHelper';
import { useInfoViewActionsContext } from '@unpod/providers';
import {
  StyledActionBar,
  StyledContent,
  StyledCoverWrapper,
  StyledDelContainer,
  StyledDivider,
  StyledMediaWrapper,
  StyledTagsSelect,
  StyledTitleInput,
  StyledTitleWrapper,
  StyleExtraSpace,
} from './index.styled';
import { getLocalizedOptions } from '@unpod/helpers/LocalizationFormatHelper';
import { useIntl } from 'react-intl';

const { Title } = Typography;
const { Option } = Select;
const acceptTypes = '.png, .jpg, .jpeg';

const CommonFields = ({
  queryTitle,
  setQueryTitle,
  content,
  setContent,
  tags,
  setTags,
  tagsData,
  currentPrivacy,
  setPrivacyType,
  userList,
  setUserList,
  coverUploadPercent,
  coverPreviewUrl,
  setCoverPreviewUrl,
  coverImage,
  setCoverImage,
  isSubEnabled,
  setThreadType,
  submitRequest,
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [open, setOpen] = useState(false);
  const { formatMessage } = useIntl();

  const onTitleChange = (e) => {
    const newTitle = e.target.value;
    setQueryTitle(newTitle);
  };

  const onRemoveCoverImage = () => {
    setCoverPreviewUrl(null);
    setCoverImage(null);
  };

  const handleCoverImageChange = (file) => {
    const extension = getFileExtension(file.name);
    if (
      acceptTypes &&
      !acceptTypes.includes(extension) &&
      (!file.type ||
        (!acceptTypes.includes(file.type) &&
          !acceptTypes?.split('/').includes(file.type?.split('/')[0])))
    ) {
      infoViewActionsContext.showError(`File type is now allowed`);
    } else {
      setCoverPreviewUrl(window.URL.createObjectURL(file));
      setCoverImage(file);
    }

    return false;
  };

  const onShareChange = (option) => {
    setPrivacyType(option.key);

    if (option.key === 'shared') {
      setOpen(true);
    }
  };

  return (
    <Fragment>
      {coverUploadPercent > 0 && coverUploadPercent < 100 ? (
        <StyledMediaWrapper>
          <Title level={4} type="secondary" className="mb-0">
            Cover Image
          </Title>
          <Progress percent={coverUploadPercent} />
        </StyledMediaWrapper>
      ) : (
        !!coverPreviewUrl && (
          <StyledMediaWrapper>
            <StyledCoverWrapper>
              <AppImage
                src={coverPreviewUrl}
                alt="Cover Image"
                layout="fill"
                objectFit="cover"
              />
            </StyledCoverWrapper>

            {coverImage && (
              <StyledDelContainer>
                <MdClear
                  fontSize={16}
                  onClick={onRemoveCoverImage}
                  className="remove-cover-handle"
                />
              </StyledDelContainer>
            )}
          </StyledMediaWrapper>
        )
      )}

      <StyledTitleWrapper>
        <StyledTitleInput
          placeholder="Title"
          value={queryTitle}
          onChange={onTitleChange}
          maxLength={100}
          variant="borderless"
          className="title-input"
        />
      </StyledTitleWrapper>

      <StyledDivider />

      <StyledContent>
        <AppMarkdownEditor
          value={content}
          onChange={setContent}
          rows={24}
          bordered={false}
        />
      </StyledContent>

      {content && (
        <Fragment>
          <StyledDivider />

          <StyledTagsSelect
            placeholder="Tags"
            mode="tags"
            variant="borderless"
            value={tags}
            onChange={setTags}
          >
            {tagsData?.data?.map((item) => (
              <Option key={item.name} value={item.name}>
                {item.name}
              </Option>
            ))}
          </StyledTagsSelect>
        </Fragment>
      )}

      <StyleExtraSpace />

      <StyledActionBar>
        <Space>
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
              <Button shape="round" icon={currentPrivacy?.icon}>
                {formatMessage({id:currentPrivacy?.label})}
              </Button>
            </Dropdown>
          </PostPermissionPopover>

          <Upload
            name="file"
            accept={acceptTypes}
            maxCount={1}
            beforeUpload={handleCoverImageChange}
            multiple={false}
            showUploadList={false}
          >
            <Badge dot={coverPreviewUrl} offset={[-7, 5]}>
              <Button
                type="default"
                shape="round"
                icon={<MdOutlineImage fontSize={24} />}
              />
            </Badge>
          </Upload>
        </Space>

        <Space>
          {/*<Button shape="round" onClick={() => onCancel()}>
            Cancel
          </Button>*/}

          <Button
            type="primary"
            shape="round"
            onClick={() => setThreadType('')}
            ghost
          >
            Cancel
          </Button>
          <Button
            type="primary"
            shape="round"
            onClick={() => submitRequest('draft')}
            disabled={!isSubEnabled}
            ghost
          >
            Save Draft
          </Button>

          <Button
            type="primary"
            shape="round"
            onClick={() => submitRequest('published')}
            disabled={!isSubEnabled}
          >
            Publish
          </Button>
        </Space>
      </StyledActionBar>
    </Fragment>
  );
};

const { bool, func, string, array, object, number } = PropTypes;

CommonFields.propTypes = {
  queryTitle: string,
  setQueryTitle: func,
  content: string,
  setContent: func,
  tags: array,
  setTags: func,
  tagsData: object,
  currentPrivacy: object,
  setPrivacyType: func,
  userList: array,
  setUserList: func,
  coverUploadPercent: number,
  coverPreviewUrl: string,
  setCoverPreviewUrl: func,
  coverImage: object,
  setCoverImage: func,
  isSubEnabled: bool,
  submitRequest: func,
};

export default CommonFields;
