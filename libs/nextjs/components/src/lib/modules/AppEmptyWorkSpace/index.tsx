import {StyledPlaceHolder, StyledPlaceHolderInner} from './index.styled';
import AppImage from '../../next/AppImage';
import type {ReactNode} from 'react';
import {Typography} from 'antd';

import {useIntl} from 'react-intl';

const emptyMessages = {
  space: {
    titleId: 'empty.spaceTitle',
    descriptionId: 'empty.spaceSescription',
  },
  kb: {
    titleId: 'empty.kbTitle',
    descriptionId: 'empty.kbDescription',
  },
  post: {
    titleId: 'empty.postTitle',
    descriptionId: 'empty.postDescription',
  },
  note: {
    titleId: 'empty.noteTitle',
    descriptionId: 'empty.noteDescription',
  },
  org: {
    titleId: 'empty.orgTitle',
    descriptionId: 'empty.orgDescription',
  },
};

type EmptyType = keyof typeof emptyMessages;

type AppEmptyWorkSpaceProps = {
  type?: EmptyType;
  children?: ReactNode;
  title?: string;
};

const AppEmptyWorkSpace = ({
                             type = 'space',
                             children,
                             title,
                           }: AppEmptyWorkSpaceProps) => {
  const {formatMessage} = useIntl();

  const message = type ? emptyMessages[type] : undefined;

  return (
    <StyledPlaceHolder>
      <StyledPlaceHolderInner>
        <AppImage
          src={'/images/design-team.png'}
          alt="Design Team"
          width={children ? 320 : 376}
          height={children ? 280 : 344}
        />

        <Typography.Title level={2} style={{marginTop: 32}}>
          {message ? formatMessage({id: message.titleId}) : title}
        </Typography.Title>

        {message?.descriptionId && (
          <Typography.Paragraph type="secondary">
            {formatMessage({
              id: message.descriptionId,
            })}
          </Typography.Paragraph>
        )}
      </StyledPlaceHolderInner>

      {children}
    </StyledPlaceHolder>
  );
};

export default AppEmptyWorkSpace;
