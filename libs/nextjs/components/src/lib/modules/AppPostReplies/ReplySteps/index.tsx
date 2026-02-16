import { memo } from 'react';

import { Space, Timeline, Tooltip, Typography } from 'antd';
import {
  changeDateStringFormat,
  getTimeFromNow,
} from '@unpod/helpers/DateHelper';
import {
  StyledAvatar,
  StyledContainer,
  StyledContent,
  StyledMeta,
  StyledMetaContent,
  StyledMetaTitle,
  StyledReplyContainer,
  StyledSystemMessage,
  StyledTime,
  StyledTitle,
} from '../index.styled';
import {
  MdAutorenew,
  MdDoneAll,
  MdInput,
  MdList,
  MdSearch,
} from 'react-icons/md';
import UserAvatar from '../../../common/UserAvatar';
import { useIntl } from 'react-intl';

type ReplyStep = {
  step: string | number;
  task_name?: string;
};

const ReplySteps = ({ reply }: { reply: any }) => {
  const { formatMessage } = useIntl();
  return (
    <StyledReplyContainer>
      <StyledAvatar>
        <UserAvatar user={reply.user} />
      </StyledAvatar>

      <StyledContent>
        <StyledMeta>
          <StyledMetaContent>
            <StyledMetaTitle>
              <StyledTitle>{reply.user.full_name}</StyledTitle>
              <Tooltip
                title={changeDateStringFormat(
                  reply.created,
                  'YYYY-MM-DD HH:mm:ss',
                  'hh:mm A . DD MMM, YYYY',
                )}
              >
                <StyledTime type="secondary">
                  {getTimeFromNow(reply.created)}
                </StyledTime>
              </Tooltip>
            </StyledMetaTitle>
          </StyledMetaContent>

          <StyledSystemMessage>
            <Space>
              <MdSearch fontSize={18} />
              <Typography.Text>
                <Typography.Text strong>
                  {formatMessage({ id: 'reply.action' })}:
                </Typography.Text>{' '}
                {formatMessage({ id: 'reply.search' })}
              </Typography.Text>
            </Space>
            <Space>
              <MdInput fontSize={18} />
              <Typography.Text>
                <Typography.Text strong>
                  {formatMessage({ id: 'reply.actionInput' })}:
                </Typography.Text>{' '}
                {formatMessage({ id: 'reply.sampleQuery' })}
              </Typography.Text>
            </Space>
            <Space>
              <MdList fontSize={18} />
              <Typography.Text>
                <Typography.Text strong>
                  {formatMessage({ id: 'reply.observation' })}:
                </Typography.Text>{' '}
                {formatMessage({ id: 'reply.sampleObservation' })}
              </Typography.Text>
            </Space>
            <Space>
              <MdAutorenew fontSize={18} />
              <Typography.Text>
                <Typography.Text strong>
                  {formatMessage({ id: 'reply.thought' })}:
                </Typography.Text>{' '}
                {formatMessage({ id: 'reply.sampleThought' })}
              </Typography.Text>
            </Space>
            <Space>
              <MdDoneAll fontSize={18} />
              <Typography.Text>
                <Typography.Text strong>
                  {formatMessage({ id: 'reply.finalAnswer' })}:
                </Typography.Text>{' '}
                {formatMessage({ id: 'reply.sampleFinalAnswer' })}
              </Typography.Text>
            </Space>

            {(reply.data?.steps || []).map((task: ReplyStep) => (
              <Space key={task.step}>
                <MdSearch fontSize={18} />
                <Typography.Text>{task.task_name}</Typography.Text>
              </Space>
            ))}
          </StyledSystemMessage>

          <StyledContainer>
            <Timeline>
              <Timeline.Item dot={<MdSearch fontSize={18} />}>
                <Typography.Text>
                  <Typography.Text strong>
                    {formatMessage({ id: 'reply.action' })}:
                  </Typography.Text>{' '}
                  {formatMessage({ id: 'reply.search' })}
                </Typography.Text>
              </Timeline.Item>

              <Timeline.Item dot={<MdInput fontSize={18} />}>
                <Typography.Text>
                  <Typography.Text strong>
                    {formatMessage({ id: 'reply.actionInput' })}:
                  </Typography.Text>{' '}
                  {formatMessage({ id: 'reply.sampleQuery' })}
                </Typography.Text>
              </Timeline.Item>

              <Timeline.Item dot={<MdList fontSize={18} />}>
                <Typography.Text>
                  <Typography.Text strong>
                    {formatMessage({ id: 'reply.actionInput' })}:
                  </Typography.Text>{' '}
                  {formatMessage({ id: 'reply.sampleObservation' })}
                </Typography.Text>
              </Timeline.Item>

              <Timeline.Item dot={<MdAutorenew fontSize={18} />}>
                <Typography.Text>
                  <Typography.Text strong>
                    {' '}
                    {formatMessage({ id: 'reply.thought' })}:
                  </Typography.Text>{' '}
                  {formatMessage({ id: 'reply.sampleThought' })}
                </Typography.Text>
              </Timeline.Item>

              <Timeline.Item dot={<MdDoneAll fontSize={18} />}>
                <Typography.Text>
                  <Typography.Text strong>
                    {formatMessage({ id: 'reply.actionInput' })}:
                  </Typography.Text>{' '}
                  {formatMessage({ id: 'reply.sampleFinalAnswer' })}
                </Typography.Text>
              </Timeline.Item>

              {(reply.data?.steps || []).map((task: ReplyStep) => (
                <Timeline.Item key={task.step} dot={<MdSearch fontSize={18} />}>
                  <Typography.Text>{task.task_name}</Typography.Text>
                </Timeline.Item>
              ))}
            </Timeline>
          </StyledContainer>
        </StyledMeta>
      </StyledContent>
    </StyledReplyContainer>
  );
};

export default memo(ReplySteps);
