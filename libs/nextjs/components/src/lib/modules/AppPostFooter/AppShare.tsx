import {useState} from 'react';
import {TbShare3} from 'react-icons/tb';
import {Divider, Space, Typography} from 'antd';
import styled from 'styled-components';
import AppCopyToClipboard from '../../third-party/AppCopyToClipboard';

import {SITE_URL} from '@unpod/constants';
import {AppPopover} from '../../antd';
import {useInfoViewActionsContext} from '@unpod/providers';
import {useIntl} from 'react-intl';

export const StyledItemWrapper = styled(Space)`
  cursor: pointer;
  user-select: none;

  &:hover .ant-typography {
    color: ${({theme}) => theme.palette.primary};
  }
`;
export const StyledShareItemWrapper = styled(Space)`
  cursor: pointer;
  user-select: none;
`;
export type PostShare = {
  slug?: string;
  title?: string;
  content?: string;
};

const getLinkText = (post?: PostShare) => `${SITE_URL}/thread/${post?.slug}/`;

const AppShare = ({post}: { post?: PostShare }) => {
  const [open, setOpen] = useState(false);
  const infoViewActionsContext = useInfoViewActionsContext();
  const {formatMessage} = useIntl();

  const onClose = () => {
    setOpen(false);
  };

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
  };

  const onShare = () => {
    onClose();

    if (typeof navigator !== 'undefined' && 'share' in navigator) {
      navigator
        .share({
          title: post?.title || '',
          text: post?.content || '',
          url: getLinkText(post),
        })
        .then(() => {
          infoViewActionsContext.showMessage(
            formatMessage({id: 'common.shareSuccess'}),
          );
        })
        .catch((error) => {
          infoViewActionsContext.showError(
            error || formatMessage({id: 'common.somethingWentWrong'}),
          );
        });
    }
  };

  return (
    <StyledItemWrapper>
      <AppPopover
        placement="left"
        open={open}
        onOpenChange={handleOpenChange}
        content={
          <>
            <AppCopyToClipboard
              text={getLinkText(post)}
              onCopy={() => {
                onClose();
              }}
              title={formatMessage({id: 'common.copyLink'})}
            />
            {typeof navigator !== 'undefined' && 'share' in navigator && (
              <>
                <Divider
                  style={{
                    margin: '8px 0',
                  }}
                />

                <StyledShareItemWrapper onClick={onShare}>
                  {formatMessage({id: 'common.shareLink'})}
                </StyledShareItemWrapper>
              </>
            )}
          </>
        }
        getPopupContainer={(trigger) => trigger.parentElement || document.body}
      >
        <Typography.Text type="secondary">
          <TbShare3 fontSize={20}/>
        </Typography.Text>
      </AppPopover>
    </StyledItemWrapper>
  );
};

export default AppShare;

