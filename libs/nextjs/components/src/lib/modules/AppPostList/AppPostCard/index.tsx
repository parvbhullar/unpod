import type { MouseEvent } from 'react';

import { Badge, Space, Tooltip, Typography } from 'antd';
import { FaPlay } from 'react-icons/fa';
import AppImage from '../../../next/AppImage';
import {
  changeDateStringFormat,
  getTimeFromNow,
} from '@unpod/helpers/DateHelper';
import { getPostIcon } from '@unpod/helpers/PermissionHelper';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import { getImageUrl } from '@unpod/helpers/UrlHelper';
import {
  StyledMeta,
  StyledPlayWrapper,
  StyledPostMedia,
  StyledRoot,
  StyledThumbnailWrapper,
} from './index.styled';
import AppLink from '../../../next/AppLink';
import { useIntl } from 'react-intl';
import type { Thread } from '@unpod/constants/types';

const { Paragraph, Text, Title } = Typography;

type AppPostCardProps = {
  thread: Thread;
  onThreadClick: (thread: Thread) => void;};

const AppPostCard = ({ thread, onThreadClick }: AppPostCardProps) => {
  const { formatMessage } = useIntl();
  const onTitleClick = (event: MouseEvent<HTMLElement>) => {
    event.preventDefault();

    onThreadClick(thread);
  };
  const firstReplyMedia = thread?.block?.data?.files?.find(
    (reply: { file_type?: string }) => reply.file_type === 'image',
  );

  const postTitle =
    thread.title === formatMessage({ id: 'thread.noTitle' }) ||
    thread.title === formatMessage({ id: 'thread.writeTitle' }) ||
    thread.title === formatMessage({ id: 'thread.uploadTitle' })
      ? getStringFromHtml(thread.content || thread.block?.data?.content)
      : thread.title;

  return (
    <StyledRoot onClick={onTitleClick}>
      <StyledMeta>
        <AppLink href={`/thread/${thread.slug}/`}>
          <Title
            level={3}
            className={'font-weight-medium'}
            style={{
              fontSize: 18,
              lineHeight: 1.2,
            }}
            ellipsis={{
              rows: 1,
              tooltip: postTitle,
            }}
          >
            {postTitle}
          </Title>
        </AppLink>

        <Paragraph className="mb-0" type="secondary" ellipsis={{ rows: 2 }}>
          {getStringFromHtml(thread.content || thread.block?.data?.content)}
        </Paragraph>
        <Paragraph style={{ fontSize: 13, marginBottom: 0 }}>
          <Space align="center" wrap={true}>
            <Text className="text-capitalize">{thread?.user?.full_name}</Text>
            <Tooltip title={thread?.privacy_type}>
              <span style={{ display: 'inline-flex', marginTop: 6 }}>
                {getPostIcon(thread?.privacy_type || '')}
              </span>
            </Tooltip>
            {thread.seen ? null : <Badge color="#796cff" />}

            {thread.created ? (
              <Tooltip
                title={changeDateStringFormat(
                  thread.created,
                  'YYYY-MM-DD HH:mm:ss',
                  'hh:mm A . DD MMM, YYYY',
                )}
              >
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {getTimeFromNow(thread.created)}
                </Text>
              </Tooltip>
            ) : null}
          </Space>
        </Paragraph>
      </StyledMeta>

      {(thread.media || thread.cover_image || firstReplyMedia) && (
        <StyledPostMedia>
          {thread.media ? (
            <StyledThumbnailWrapper>
              <AppImage
                src={
                  thread.cover_image
                    ? `${thread.cover_image?.url}?tr=w-140,h-90`
                    : thread.media.media_type === 'audio'
                      ? getImageUrl('music.svg')
                      : `https://image.mux.com/${thread.media.playback_id}/thumbnail.jpg?width=290&height=160`
                }
                alt={thread.title}
                height={160}
                width={290}
                layout="fill"
                objectFit="cover"
              />
              <StyledPlayWrapper>
                <FaPlay />
              </StyledPlayWrapper>
            </StyledThumbnailWrapper>
          ) : (
            (thread.cover_image || firstReplyMedia) && (
              <StyledThumbnailWrapper>
                <AppImage
                  src={`${
                    thread.cover_image?.url || firstReplyMedia?.url
                  }?tr=w-290,h-180`}
                  alt={thread.title}
                  height={180}
                  width={290}
                  layout="fill"
                  objectFit="cover"
                />
              </StyledThumbnailWrapper>
            )
          )}
        </StyledPostMedia>
      )}
    </StyledRoot>
  );
};

export default AppPostCard;
