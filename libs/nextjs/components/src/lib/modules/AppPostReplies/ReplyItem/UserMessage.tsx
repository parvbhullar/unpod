import type { ReactNode } from 'react';
import { Fragment } from 'react';
import clsx from 'clsx';
import {
  StyledAvatar,
  StyledContentWrapper,
  StyledParent,
  StyledReplyParent,
  StyledTime,
  StyledUserActions,
  StyledUserContainer,
  StyledUserContent,
  StyledUserMeta,
  StyledUserQuestion,
} from '../index.styled';
import {
  Button,
  Divider,
  Dropdown,
  Grid,
  Space,
  Tooltip,
  Typography,
} from 'antd';
import UserAvatar from '../../../common/UserAvatar';
import { BsArrowReturnLeft } from 'react-icons/bs';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import {
  changeDateStringFormat,
  getTimeFromNow,
} from '@unpod/helpers/DateHelper';
import ReactHtmlParser from '@unpod/external-libs/react-render-html';
import ContentWithSource from './ContentWithSource';
import AppMarkdownViewer from '../../../third-party/AppMarkdownViewer';
import AppJsonViewer from '../../../third-party/AppJsonViewer';
import ImageGallery from '../../../common/ImageGallery';
import AppAttachments from '../../../common/AppAttachments';
import AppMediaPlayer from '../../../common/AppMediaPlayer';
import { MdMoreVert, MdOutlineAccessTime } from 'react-icons/md';
import AppPostFooter from '../../AppPostFooter';
import { getAvatarIconSize, getAvatarSize, getIconSize } from '../IconSize';
import { useMediaQuery } from 'react-responsive';
import { MobileWidthQuery } from '@unpod/constants';

const { Paragraph, Text } = Typography;

const { useBreakpoint } = Grid;

const UserMessage = ({
  reply,
  replyParent,
  onClapClick,
  onReplyClick,
  onMenuClick,
  items,
  isAuthenticated,
  user,
  attachmentImages,
  attachmentFiles,
  onDownloadClick,
  children,
  hideReply = false,
  hideDelete = false,
}: {
  reply: any;
  replyParent?: any;
  onClapClick?: (
    reply: any,
    reactionCount: number,
    isSubReply?: boolean,
    parentReply?: any,
  ) => void;
  onReplyClick?: (reply: any) => void;
  onMenuClick?: (key: any, block: any) => void;
  items?: any;
  isAuthenticated?: boolean;
  user?: any;
  attachmentImages?: any[];
  attachmentFiles?: any[];
  onDownloadClick?: (item: any) => void;
  onSaveNote?: (data: any) => void;
  noteTitle?: string | null;
  actionsStyle?: any;
  onClickName?: () => void;
  children?: ReactNode;
  hideReply?: boolean;
  hideDelete?: boolean;
}) => {
  const screens = useBreakpoint();
  const isOwn = reply.user.user_id === user?.id;
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const avatarSize = getAvatarSize(screens);
  const avatarIconSize = getAvatarIconSize(screens);
  const iconSize = getIconSize(screens);

  return (
    <StyledUserContainer
      className={clsx({
        'user-question': reply.user.user_token,
      })}
    >
      <StyledUserContent
        style={{
          textAlign: isOwn ? 'right' : undefined,
          alignItems: isOwn ? 'flex-end' : undefined,
        }}
      >
        <StyledUserMeta>
          {/*<StyledMetaContent>
            <StyledMetaTitle>
              <StyledTitle className="text-capitalize">
                {reply.user.full_name}
              </StyledTitle>
              <Tooltip
                title={changeDateStringFormat(
                  reply.created,
                  'YYYY-MM-DD HH:mm:ss',
                  'hh:mm A . DD MMM, YYYY'
                )}
              >
                <StyledTime type="secondary">
                  {getTimeFromNow(reply.created)}
                </StyledTime>
              </Tooltip>
            </StyledMetaTitle>

            <StyledActions style={actionsStyle}>
              <AppPostFooter
                post={reply}
                onClapClick={
                  onClapClick
                    ? (count: number) => onClapClick(reply, count)
                    : undefined
                }
                clapCount={reply.reaction_count}
                commentCount={reply.reply_count}
                activeComment={replyParent?.slug === reply.slug}
                onCommentClick={() => {
                  onReplyClick?.(reply);
                }}
                copyContent={reply.data?.content}
              >
                {isAuthenticated && reply.user.user_id === user?.id && (
                  <Dropdown
                    menu={{
                      items: items,
                      onClick: (item) => {
                        item.domEvent.stopPropagation();
                        onMenuClick(item.key, reply);
                      },
                    }}
                    placement="bottomRight"
                  >
                    <Button
                      size="small"
                      type={'link'}
                      shape="circle"
                      icon={<MdMoreVert fontSize={24} />}
                    />
                  </Dropdown>
                )}
              </AppPostFooter>
            </StyledActions>
          </StyledMetaContent>*/}

          {reply.parent?.block_id && (
            <StyledReplyParent>
              <StyledParent>
                <BsArrowReturnLeft fontSize={16} />
                <Paragraph type="secondary" ellipsis>
                  {reply.parent.title
                    ? reply.parent.title
                    : getStringFromHtml(reply.parent?.data?.content)}
                </Paragraph>
              </StyledParent>

              <Space>
                <UserAvatar
                  user={reply.parent.user}
                  size={24}
                  style={{ fontSize: 10 }}
                />
                <Text>{reply.parent.user.full_name}</Text>
                <StyledTime type="secondary">
                  {getTimeFromNow(reply.parent.created)}
                </StyledTime>
              </Space>
            </StyledReplyParent>
          )}

          {reply.block === 'html' || reply.block === 'text' ? (
            <Fragment>
              {reply.data?.content &&
                (reply.user.user_token ? (
                  <StyledUserQuestion>
                    {ReactHtmlParser(reply.data.content)}
                  </StyledUserQuestion>
                ) : reply.data.metadata ? (
                  <ContentWithSource reply={reply} />
                ) : (
                  <StyledContentWrapper>
                    <AppMarkdownViewer markdown={reply.data.content} />
                  </StyledContentWrapper>
                ))}

              {reply.data?.json && (
                <AppJsonViewer json={reply.data.json} showCopyClipboard />
              )}

              {attachmentImages && attachmentImages?.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <ImageGallery
                    images={(attachmentImages || []) as { media_url: string }[]}
                    onDownload={
                      onDownloadClick
                        ? (item, _event) => onDownloadClick(item)
                        : undefined
                    }
                  />
                </div>
              )}

              {attachmentFiles && attachmentFiles.length > 0 && (
                <Fragment>
                  <Divider type="horizontal" style={{ marginBlock: 12 }} />
                  <AppAttachments
                    attachments={(attachmentFiles || []) as any}
                    onDownload={onDownloadClick}
                  />
                </Fragment>
              )}
            </Fragment>
          ) : (
            reply.block === 'media' && (
              <div className="app-post-viewer">
                <AppMediaPlayer title={reply.title} media={reply.media} />
              </div>
            )
          )}

          {children}
        </StyledUserMeta>

        <StyledUserActions
          style={{
            justifyContent: isOwn ? 'flex-start' : 'flex-end',
          }}
        >
          <AppPostFooter
            post={reply}
            onClapClick={
              onClapClick
                ? (count: number) => onClapClick(reply, count)
                : undefined
            }
            clapCount={reply.reaction_count}
            commentCount={reply.reply_count}
            activeComment={replyParent?.slug === reply.slug}
            onCommentClick={() => {
              onReplyClick?.(reply);
            }}
            copyContent={reply.block !== 'html' && reply.data?.content}
            hideComment={hideReply || reply.block === 'html'}
          >
            {!hideDelete &&
              isAuthenticated &&
              reply.user.user_id === user?.id && (
                <Dropdown
                  menu={{
                    items: items,
                    onClick: (item) => {
                      item.domEvent.stopPropagation();
                      onMenuClick?.(item.key, reply);
                    },
                  }}
                  placement="bottomRight"
                  getPopupContainer={(triggerNode) =>
                    triggerNode.parentElement || document.body
                  }
                >
                  <Button
                    size="small"
                    type={'link'}
                    shape="circle"
                    icon={<MdMoreVert fontSize={avatarIconSize} />}
                  />
                </Dropdown>
              )}
          </AppPostFooter>

          <Tooltip
            title={changeDateStringFormat(
              reply.created,
              'YYYY-MM-DD HH:mm:ss',
              'hh:mm A . DD MMM, YYYY',
            )}
          >
            <StyledTime type="secondary">
              <MdOutlineAccessTime fontSize={iconSize} />
              {getTimeFromNow(reply.created)}
            </StyledTime>
          </Tooltip>
        </StyledUserActions>
      </StyledUserContent>
      {!mobileScreen ? (
        <StyledAvatar>
          {reply.user.user_token ? (
            <Tooltip title={reply.user.full_name}>
              <UserAvatar
                size={avatarSize}
                allowRandom={false}
                user={
                  reply.user?.user_id === user?.id
                    ? {
                        ...user,
                        // profile_color: user?.user_detail?.profile_color,
                      }
                    : reply.user
                }
              />
            </Tooltip>
          ) : (
            <Tooltip title={reply.user.full_name}>
              {reply.user.user_id === 'super-ai' ||
              reply.user.user_id === 'assistant' ? (
                <UserAvatar
                  size={avatarSize}
                  src="/images/unpod/logo-icon.svg"
                  bgColor="transparent"
                />
              ) : (
                <UserAvatar
                  size={avatarSize}
                  allowRandom={false}
                  user={reply.user}
                />
              )}
            </Tooltip>
          )}
        </StyledAvatar>
      ) : null}
    </StyledUserContainer>
  );
};

export default UserMessage;
