import { memo } from 'react';

import { Button, Divider, Tooltip, Typography } from 'antd';
import { RxExternalLink } from 'react-icons/rx';
import { MdLink } from 'react-icons/md';
import {
  changeDateStringFormat,
  getTimeFromNow,
} from '@unpod/helpers/DateHelper';
import { getDataApi, useInfoViewActionsContext } from '@unpod/providers';
import { downloadFile } from '@unpod/helpers/FileHelper';
import AppMarkdownViewer from '../../../../third-party/AppMarkdownViewer';
import UserAvatar from '../../../../common/UserAvatar';
import {
  StyledAvatarWrapper,
  StyledCollapsedMeta,
  StyledContent,
  StyledDetailsItems,
  StyledHeaderExtra,
  StyledListHeader,
  StyledMeta,
} from './index.styled';
import type { Document } from '@unpod/constants/types';

const { Paragraph, Text, Title } = Typography;

const DocumentView = ({ document }: { document: Document }) => {
  const infoViewActionsContext = useInfoViewActionsContext();

  const onViewClick = () => {
    if (document.meta?.source_url || document.meta?.siteUrl) {
      window.open(
        document.meta?.source_url || document.meta?.siteUrl,
        '_blank',
      );
    } else {
      getDataApi('media/pre-signed-url/', infoViewActionsContext, {
        url: document.url,
      })
        .then((res: any) => {
          downloadFile(res.data.url);
        })
        .catch((response: any) => {
          infoViewActionsContext.showError(response.message);
        });
    }
  };
  const content = document.content || document.description || '';

  return (
    <StyledDetailsItems>
      <StyledListHeader>
        <StyledAvatarWrapper>
          <UserAvatar user={{ full_name: document.name }} />
        </StyledAvatarWrapper>
        <StyledMeta>
          <StyledCollapsedMeta>
            <Title level={5} className="item-title">
              {document.title}
            </Title>
            <Paragraph className="item-user-name">{document.name}</Paragraph>
          </StyledCollapsedMeta>
        </StyledMeta>
        <StyledHeaderExtra
          align="center"
          size={5}
          split={<Divider type="vertical" />}
        >
          <Tooltip
            title={changeDateStringFormat(
              document.created || '',
              'YYYY-MM-DD HH:mm:ss',
              'hh:mm A . DD MMM, YYYY',
            )}
          >
            <Text type="secondary">
              {getTimeFromNow(document.created || '')}
            </Text>
          </Tooltip>

          <Tooltip title="View">
            <Button
              type="text"
              size="small"
              shape="circle"
              onClick={onViewClick}
            >
              <RxExternalLink fontSize={18} />
            </Button>
          </Tooltip>
        </StyledHeaderExtra>
      </StyledListHeader>
      <StyledContent>
        <AppMarkdownViewer
          markdown={content}
          components={{
            a: ({ children, ...props }: any) => {
              return (
                <a {...props} target="_blank" rel="noopener noreferrer">
                  {children || <MdLink />}
                </a>
              );
            },
          }}
        />
      </StyledContent>
    </StyledDetailsItems>
  );
};

export default memo(DocumentView);
