import {Button, Space} from 'antd';
import {type ReactNode, useState} from 'react';
import {FiMoreVertical} from 'react-icons/fi';
import {downloadFile} from '@unpod/helpers/FileHelper';
import AppConfirmDeletePopover from '../../antd/AppConfirmDeletePopover';
import AppIcon from '../AppIcon';
import {StyledTableActions} from './index.styled';
import {AppPopover} from '../../antd';
import {useIntl} from 'react-intl';

type AppTableActionsProps = {
  onEdit?: () => void;
  onDelete?: () => void;
  showToolTip?: boolean;
  onPreview?: () => void;
  downloadUrl?: string;
  children?: ReactNode;
  endComponents?: ReactNode;
  deleteTitle?: string;
  deleteMessage?: string;
  alignRight?: boolean;
};

export const AppTableActions = ({
                                  onEdit,
                                  onDelete,
                                  showToolTip = false,
                                  onPreview,
                                  downloadUrl,
                                  children,
                                  endComponents,
                                  deleteTitle = 'common.deleteMessage',
                                  deleteMessage,
                                  alignRight,
                                }: AppTableActionsProps) => {
  const [open, setOpen] = useState(false);
  const {formatMessage} = useIntl();

  const onHide = () => {
    setOpen(false);
  };

  const onHandleChange = (newState: boolean) => {
    setOpen(newState);
  };

  const getItem = () => {
    return (
      <Space
        direction={showToolTip ? 'horizontal' : 'vertical'}
        className="table-action-items"
        onClick={
          showToolTip
            ? () => {
              console.log('onClick');
            }
            : onHide
        }
      >
        {children}

        {downloadUrl && (
          <AppIcon
            title={formatMessage({id: 'common.download'})}
            up-role="Download"
            icon="download"
            onClick={() => downloadFile(downloadUrl)}
          />
        )}
        {onPreview ? (
          <AppIcon
            title={formatMessage({id: 'common.view'})}
            up-role="View"
            icon="view"
            onClick={onPreview}
          />
        ) : null}

        {onEdit && (
          <AppIcon
            title={formatMessage({id: 'common.edit'})}
            icon="edit"
            onClick={onEdit}
            up-role={'Edit'}
          />
        )}

        {onDelete && (
          <AppConfirmDeletePopover
            title={formatMessage({id: deleteTitle})}
            message={deleteMessage}
            onConfirm={() => onDelete?.()}
          >
            <AppIcon
              icon="delete"
              title="Delete"
              up-role="Delete"
              placement="leftTop"
            />
          </AppConfirmDeletePopover>
        )}

        {endComponents}
      </Space>
    );
  };
  return (
    <StyledTableActions
      className={`${alignRight ? 'align-right' : ''} app-table-actions`}
    >
      {showToolTip ? (
        getItem()
      ) : (
        <AppPopover
          placement="leftTop"
          content={getItem()}
          open={open}
          rootClassName={open ? 'active-popover' : ''}
          onOpenChange={onHandleChange}
        >
          <Button
            type="text"
            shape="circle"
            className={'app-table-more-actions'}
            onClick={() => onHandleChange(true)}
          >
            <FiMoreVertical
              fontSize={20}
              style={{
                cursor: 'pointer',
              }}
              role="button"
            />
          </Button>
        </AppPopover>
      )}
    </StyledTableActions>
  );
};
export default AppTableActions;
