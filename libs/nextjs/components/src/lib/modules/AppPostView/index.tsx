import type {CSSProperties} from 'react';
import {Fragment, memo, useEffect, useState} from 'react';

import type {MenuProps} from 'antd';
import {Badge, Button, Divider, Dropdown, Grid, Image, Space, Tooltip, Typography,} from 'antd';
import {MdMoreVert, MdOutlineAccessTime} from 'react-icons/md';
import AppImage from '../../next/AppImage';
import {changeDateStringFormat, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {getThreadMenu} from '@unpod/helpers/PermissionHelper';
import {getDataApi, useAuthContext, useInfoViewActionsContext,} from '@unpod/providers';
import {POST_TYPE} from '@unpod/constants/AppEnums';
import {downloadFile} from '@unpod/helpers/FileHelper';
import UserAvatar from '../../common/UserAvatar';
import AppMediaPlayer from '../../common/AppMediaPlayer';
import AppPostFooter from '../AppPostFooter';
import ImageGallery from '../../common/ImageGallery';
import AppAttachments from '../../common/AppAttachments';
import AppMarkdownViewer from '../../third-party/AppMarkdownViewer';
import ReferenceDataView from './ReferenceDataView';
import {
  StyledActionsWrapper,
  StyledAvatarWrapper,
  StyledContainer,
  StyledContent,
  StyledContentWrapper,
  StyledDetailsItems,
  StyledHeaderContainer,
  StyledPostTitle,
  StyledThumbnailsWrapper,
  StyledTimeText,
  StyledTitleContainer,
  StyledTitleRow,
} from './index.styled';

const {Paragraph} = Typography;

const {useBreakpoint} = Grid;

const iconSizeByBreakpoint = {
  xs: 12,
  sm: 18,
  md: 18,
  lg: 18,
  xl: 18,
  xxl: 18,
};

type AppPostViewProps = {
  post: any;
  onClapClick?: (count: number) => void;
  onMenuClick?: (key: any, post: any) => void;
  onReplyPost?: (post: any) => void;
  isStreamView?: boolean;
  rootStyle?: CSSProperties;
  lastMessage?: any;
  setCurrentPost?: (post: any) => void;
};

const AppPostView = ({
                       post,
                       onClapClick,
                       onMenuClick,
                       onReplyPost,
                       isStreamView,
                       rootStyle,
                       lastMessage,
                       setCurrentPost,
                     }: AppPostViewProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const {user} = useAuthContext();
  const items = (getThreadMenu(post, user) as MenuProps['items']) || [];
  const [visible, setVisible] = useState(false);
  const screens = useBreakpoint();

  const currentKey =
    (
      Object.keys(iconSizeByBreakpoint) as Array<
        keyof typeof iconSizeByBreakpoint
      >
    ).find((key) => screens[key]) || 'lg';

  const iconSize = iconSizeByBreakpoint[currentKey];

  useEffect(() => {
    if (lastMessage?.data) {
      const data = JSON.parse(lastMessage?.data);
      // console.log('AppPostView lastMessage data', data);
      if (data?.event === 'block') {
        // console.log('AppPostView data', data);

        if (data?.data?.block === 'metadata') {
          // console.log('AppPostView metadata', data?.data?.data);

          setCurrentPost?.({
            ...post,
            title: data?.data?.data?.title,
            // content: data?.data?.data?.description,
            tags: data?.data?.data?.tags,
          });
        }
      }
    }
  }, [lastMessage, setCurrentPost]);

  const onDownloadClick = (item: any) => {
    getDataApi('media/pre-signed-url/', infoViewActionsContext, {
      url: item.url,
    })
      .then((res: any) => {
        downloadFile(res.data.url);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const attachmentImages =
    post.attachments?.filter((item: any) => item.media_type === 'image') || [];

  const attachmentFiles =
    post.attachments
      ?.filter((item: any) => item.media_type !== 'image')
      ?.map((item: any) => ({
        ...item,
        file_type: item.media_type,
      })) || [];

  return (
    <StyledDetailsItems id={`active-post-${post.slug}`} style={rootStyle}>
      <StyledHeaderContainer>
        {!post.media && post.cover_image && (
          <StyledThumbnailsWrapper>
            <AppImage
              src={`${post.cover_image?.url}?tr=w-1080,h-180`}
              alt="Cover Image"
              layout="fill"
              objectFit="cover"
              onClick={() => setVisible(true)}
            />

            <Image
              style={{display: 'none'}}
              src={`${post.cover_image?.url}?tr=w-1080,h-180`}
              preview={{
                visible: visible,
                scaleStep: 0.5,
                src: post.cover_image?.url,
                onVisibleChange: (value) => {
                  setVisible(value);
                },
              }}
            />
          </StyledThumbnailsWrapper>
        )}

        <AppMediaPlayer
          title={post.title}
          media={post.media}
          poster={post.cover_image && `${post.cover_image.url}?tr=w-960,h-540`}
        />
      </StyledHeaderContainer>

      <StyledTitleRow>
        <StyledAvatarWrapper>
          <Tooltip title={post.user.full_name}>
            <UserAvatar user={post.user}/>
          </Tooltip>
        </StyledAvatarWrapper>
        <StyledTitleContainer>
          <StyledPostTitle>
            {post.post_type === POST_TYPE.ASK
              ? post.content || post.title
              : post.title}
          </StyledPostTitle>
        </StyledTitleContainer>
      </StyledTitleRow>

      <StyledContainer>
        {/*<StyledCollapsedHeader>
            <StyledMeta>
              <StyledCollapsedMeta>
                <Typography.Title
                  level={5}
                  className="user-title text-capitalize"
                >
                  {post.user.full_name}
                </Typography.Title>
                <Typography.Paragraph className="user-sub-title">
                  <Space
                    align="center"
                    split={
                      <Typography.Text type="secondary">.</Typography.Text>
                    }
                  >
                    <Tooltip
                      title={changeDateStringFormat(
                        post.created,
                        'YYYY-MM-DD HH:mm:ss',
                        'hh:mm A . DD MMM, YYYY'
                      )}
                    >
                      <Typography.Text type="secondary">
                        {getTimeFromNow(post.created)}
                      </Typography.Text>
                    </Tooltip>
                    {post.seen ? null : <Badge color="#796cff" />}
                  </Space>
                </Typography.Paragraph>
              </StyledCollapsedMeta>
            </StyledMeta>
          </StyledCollapsedHeader>*/}

        <ReferenceDataView post={post}/>

        <StyledContent>
          {post.content &&
            !(
              post.post_type === POST_TYPE.ASK
            ) && (
              <StyledContentWrapper>
                <AppMarkdownViewer markdown={post.content}/>
              </StyledContentWrapper>
            )}

          {attachmentImages.length > 0 && (
            <ImageGallery
              images={(attachmentImages || []) as any}
              onDownload={
                onDownloadClick ? (item) => onDownloadClick(item) : undefined
              }
            />
          )}

          {attachmentFiles.length > 0 && (
            <Fragment>
              <Divider type="horizontal" style={{margin: 0}}/>
              <AppAttachments
                attachments={(attachmentFiles || []) as any}
                onDownload={onDownloadClick}
              />
            </Fragment>
          )}

          {/*<Space size={[0, 'small']} wrap>
            {post.pilot?.name && (
              <StyledTagItem
                bordered={false}
                color="#f50"
                icon={
                  <span
                    role="img"
                    aria-label={post.pilot?.name}
                    className="anticon"
                  >
                    <BiBot fontSize={16} />
                  </span>
                }
              >
                {post.pilot?.name}
              </StyledTagItem>
            )}

            {post?.knowledge_bases?.map((kb, index) => (
              <StyledTagItem
                key={`kb-${index}`}
                bordered={false}
                color={TAG_COLORS[index % 10]}
                icon={
                  <span role="img" aria-label={kb?.name} className="anticon">
                    <MdOutlineWorkspaces fontSize={16} />
                  </span>
                }
              >
                {kb?.name}
              </StyledTagItem>
            ))}

            {post?.tags?.map((tagName, index) => (
              <StyledTagItem
                key={`tag-${index}`}
                bordered={false}
                color={TAG_COLORS[index % 10]}
                icon={
                  <span role="img" aria-label={tagName} className="anticon">
                    <AiOutlineTag />
                  </span>
                }
              >
                {tagName}
              </StyledTagItem>
            ))}
          </Space>*/}

          <StyledActionsWrapper>
            <Paragraph className="user-sub-title mb-0">
              <Space align="center">
                <MdOutlineAccessTime fontSize={iconSize}/>

                <Tooltip
                  title={changeDateStringFormat(
                    post.created,
                    'YYYY-MM-DD HH:mm:ss',
                    'hh:mm A . DD MMM, YYYY',
                  )}
                >
                  <StyledTimeText type="secondary">
                    {getTimeFromNow(post.created)}
                  </StyledTimeText>
                </Tooltip>
                {post.seen ? null : <Badge color="#796cff"/>}
              </Space>
            </Paragraph>

            <AppPostFooter
              post={post}
              onClapClick={
                onClapClick ? (count: number) => onClapClick(count) : undefined
              }
              clapCount={post.reaction_count}
              commentCount={post.reply_count}
              onCommentClick={() => {
                onReplyPost?.(post);
              }}
              isSharable
              copyContent={post.content}
            >
              {items.length > 0 && !isStreamView && (
                <Dropdown
                  menu={{
                    items: items,
                    onClick: (item) => {
                      item.domEvent.stopPropagation();
                      onMenuClick?.(item.key, post);
                    },
                  }}
                  placement="bottomRight"
                  getPopupContainer={(triggerNode) =>
                    triggerNode.parentElement || document.body
                  }
                >
                  <Button
                    size="small"
                    onClick={(e) => e.stopPropagation()}
                    type={'link'}
                    shape="circle"
                    icon={<MdMoreVert fontSize={24}/>}
                  />
                </Dropdown>
              )}
            </AppPostFooter>
          </StyledActionsWrapper>
        </StyledContent>
      </StyledContainer>
    </StyledDetailsItems>
  );
};

export default memo(AppPostView);
