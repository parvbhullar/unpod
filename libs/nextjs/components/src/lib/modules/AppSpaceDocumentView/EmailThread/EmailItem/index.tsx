import {Fragment, memo, useState} from 'react';

import {Divider, Flex, Tooltip, Typography} from 'antd';
import clsx from 'clsx';
import {MdLink} from 'react-icons/md';
import {AiOutlineTag} from 'react-icons/ai';
import {changeDateStringFormat, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {TAG_COLORS} from '@unpod/constants/AppEnums';
import {removeHtmlAndHeadTags} from '@unpod/helpers/GlobalHelper';
import {getDataApi, useInfoViewActionsContext} from '@unpod/providers';
import {downloadFile, getFileExtension} from '@unpod/helpers/FileHelper';
import AppMarkdownViewer from '../../../../third-party/AppMarkdownViewer';
import UserAvatar from '../../../../common/UserAvatar';
import AppAttachments from '../../../../common/AppAttachments';
import {
  StyledAvatarWrapper,
  StyledCollapsedMeta,
  StyledContent,
  StyledDetailsItems,
  StyledHeaderExtra,
  StyledListHeader,
  StyledMeta,
  StyledTagItem,
  StyledWrapper,
} from './index.styled';

const {Paragraph, Text, Title} = Typography;

type EmailAttachment = {
  url?: string;
  filename?: string;
  [key: string]: any;
};

type EmailMeta = {
  user?: {
    name?: string;
  };
};

type EmailItemData = {
  summary?: string;
  attachments?: EmailAttachment[];
  meta?: EmailMeta;
  date?: string;
  subject?: string;
  body?: string;
  labels?: string[];
  [key: string]: any;
};

type EmailItemProps = {
  email: EmailItemData;
  isFirst?: boolean;
  setSummary?: (summary: string) => void;
};

const EmailItem = ({email, isFirst, setSummary}: EmailItemProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isExpanded, setIsExpanded] = useState(false);

  const onDownloadClick = (item: EmailAttachment) => {
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

  if (email.summary && setSummary) setSummary(email.summary);

  const attachmentFiles =
    email.attachments?.map((item) => ({
      ...item,
      file_type: getFileExtension(item.filename),
    })) || [];

  return (
    <StyledDetailsItems className="email-item">
      <StyledListHeader onClick={() => setIsExpanded(!isExpanded)}>
        <StyledAvatarWrapper>
          <UserAvatar user={{full_name: email.meta?.user?.name}}/>
        </StyledAvatarWrapper>
        <StyledMeta>
          <StyledCollapsedMeta>
            <Title level={5} className="item-title">
              {email.subject}
            </Title>
            <Paragraph className="item-user-name">
              {email.meta?.user?.name}
            </Paragraph>
          </StyledCollapsedMeta>
        </StyledMeta>
        <StyledHeaderExtra align="center">
          <Tooltip
            title={changeDateStringFormat(
              email.date || '',
              'YYYY-MM-DD HH:mm:ss',
              'hh:mm A . DD MMM, YYYY',
            )}
          >
            <Text type="secondary">{getTimeFromNow(email.date || '')}</Text>
          </Tooltip>
        </StyledHeaderExtra>
      </StyledListHeader>

      <StyledWrapper className={clsx({expanded: isFirst || isExpanded})}>
        <StyledContent>
          <AppMarkdownViewer
            markdown={removeHtmlAndHeadTags(email.body || '')}
            components={{
              a: ({children, ...props}: any) => {
                return (
                  <a {...props} target="_blank" rel="noopener noreferrer">
                    <MdLink/>
                  </a>
                );
              },
            }}
          />
        </StyledContent>

        <Flex gap="4px 0" wrap>
          {email.labels?.map((tagName, index) => (
            <StyledTagItem
              key={index}
              bordered={false}
              color={TAG_COLORS[index % 10]}
              icon={
                <span role="img" aria-label={tagName} className="anticon">
                  <AiOutlineTag/>
                </span>
              }
            >
              {tagName}
            </StyledTagItem>
          ))}
        </Flex>

        {attachmentFiles.length > 0 && (
          <Fragment>
            <Divider type="horizontal"/>

            <AppAttachments
              attachments={attachmentFiles}
              onDownload={onDownloadClick}
            />
          </Fragment>
        )}
      </StyledWrapper>
    </StyledDetailsItems>
  );
};

export default memo(EmailItem);
