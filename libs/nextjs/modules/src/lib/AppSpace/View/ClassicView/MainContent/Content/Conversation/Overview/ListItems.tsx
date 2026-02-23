import {List} from 'antd';
import {StyledListItem, StyledListMeta} from './index.styled';

const ListItems = ({
                     title,
                     description,
                     avatar,
                     recordingButton = null,
                     contentStart = false,
                     ...props
                   }: {
  title?: any;
  description?: any;
  avatar?: any;
  recordingButton?: any;
  contentStart?: boolean;
  [key: string]: any;
}) => {
  return (
    <List itemLayout="horizontal">
      <StyledListItem key={title} {...props}>
        <StyledListMeta
          className={contentStart ? 'ContentStart' : undefined}
          avatar={avatar ? avatar : null}
          title={title ? title : ''}
          description={description ? description : ''}
        />
        {recordingButton && recordingButton}
      </StyledListItem>
    </List>
  );
};

export default ListItems;
