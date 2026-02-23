import {Badge, Skeleton, Space, Tooltip, Typography} from 'antd';
import {FaPlay} from 'react-icons/fa';
import AppImage from '../../next/AppImage';
import {changeDateStringFormat, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {getPostIcon} from '@unpod/helpers/PermissionHelper';
import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import UserAvatar from '../../common/UserAvatar';
import {
  StyledCardContentWrapper,
  StyledCardWrapper,
  StyledContentWrapper,
  StyledGridThumbnailWrapper,
  StyledHubSpaceTitle,
  StyledListItemMetaWrapper,
  StyledPlayWrapper,
  StyledThreadMeta,
  StyledTitleItem,
  StyledTitleWrapper,
} from './Grid.styled';
import type {Thread} from '@unpod/constants/types';

const {Link, Text, Title} = Typography;

type GridItemProps = {
  thread: Thread;
  onThreadClick: (thread: Thread) => void;
};

const GridItem = ({thread, onThreadClick}: GridItemProps) => {
  const firstReplyMedia = thread?.block?.data?.files?.find(
    (reply: { file_type?: string }) => reply.file_type === 'image',
  );

  return (
    <Skeleton avatar title={false} loading={thread.loading} active>
      <StyledListItemMetaWrapper>
        <StyledCardWrapper onClick={() => onThreadClick(thread)}>
          {thread.media ? (
            <StyledGridThumbnailWrapper>
              <AppImage
                src={
                  thread.cover_image
                    ? `${thread.cover_image?.url}?tr=w-720,h-404`
                    : `https://image.mux.com/${thread.media.playback_id}/thumbnail.jpg?width=720&height=404`
                }
                alt={thread.title}
                height={202}
                width={360}
                layout="fill"
                objectFit="cover"
              />
              <StyledPlayWrapper>
                <FaPlay/>
              </StyledPlayWrapper>
            </StyledGridThumbnailWrapper>
          ) : (
            (thread.cover_image || firstReplyMedia) && (
              <StyledGridThumbnailWrapper>
                <AppImage
                  src={`${
                    thread.cover_image?.url || firstReplyMedia?.url
                  }?tr=w-720,h-404`}
                  alt={thread.title}
                  height={202}
                  width={360}
                  layout="fill"
                  objectFit="cover"
                />
              </StyledGridThumbnailWrapper>
            )
          )}

          <StyledCardContentWrapper>
            <StyledTitleWrapper>
              <StyledTitleItem onClick={() => onThreadClick(thread)}>
                <Title level={5} className={'title'} ellipsis>
                  <Tooltip title={thread.title}> {thread.title}</Tooltip>
                </Title>
              </StyledTitleItem>
            </StyledTitleWrapper>
            {thread.media || thread.cover_image ? null : (
              <StyledContentWrapper>
                {getStringFromHtml(
                  thread.content || thread.block?.data?.content,
                ).slice(0, 200)}
              </StyledContentWrapper>
            )}

            <StyledThreadMeta>
              <Tooltip title={thread?.user?.full_name}>
                <UserAvatar user={thread?.user}/>
              </Tooltip>

              <Space orientation="vertical" size={4}>
                <StyledHubSpaceTitle>
                  <Link className="text-capitalize">
                    {thread?.user?.full_name}
                  </Link>
                </StyledHubSpaceTitle>

                <Space orientation="horizontal">
                  {getPostIcon(thread?.privacy_type || '')}
                  {thread.seen ? null : <Badge color="#796cff"/>}
                  {thread.created ? (
                    <Tooltip
                      title={changeDateStringFormat(
                        thread.created,
                        'YYYY-MM-DD HH:mm:ss',
                        'hh:mm A . DD MMM, YYYY',
                      )}
                    >
                      <Text
                        type="secondary"
                        style={{
                          fontSize: 12,
                        }}
                      >
                        {getTimeFromNow(thread.created)}
                      </Text>
                    </Tooltip>
                  ) : null}
                </Space>
              </Space>
            </StyledThreadMeta>
          </StyledCardContentWrapper>
        </StyledCardWrapper>
      </StyledListItemMetaWrapper>
    </Skeleton>
  );
};

export default GridItem;
