import type {ReactNode} from 'react';
import {useState} from 'react';

import type {MenuProps} from 'antd';
import {Badge, Button, Dropdown, Space, Tooltip, Typography} from 'antd';
import {
  MdCheckBoxOutlineBlank,
  MdOutlineCheckBox,
  MdOutlineDelete,
  MdOutlineEdit,
  MdOutlineMoreVert,
} from 'react-icons/md';
import clsx from 'clsx';
import {changeDateStringFormat} from '@unpod/helpers/DateHelper';
import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import {deleteDataApi, getDataApi, useInfoViewActionsContext,} from '@unpod/providers';
import UserAvatar from '../../../common/UserAvatar';
import {
  StyledContent,
  StyledContentDetails,
  StyledHeaderExtra,
  StyledItem,
  StyledListHeader,
  StyledMeta,
  StyledMetaContent,
  StyledRoot,
} from './index.styled';
import AppConfirmModal from '../../../antd/AppConfirmModal';
import {useIntl} from 'react-intl';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';
import type {Document} from '@unpod/constants/types';

const {Paragraph, Title, Text} = Typography;

const menuItems = [
  {
    key: 'edit',
    label: 'common.edit',
    icon: (
      <span className="ant-icon edit-icon">
        <MdOutlineEdit fontSize={18}/>
      </span>
    ),
  },
  {
    key: 'delete',
    label: 'common.delete',
    icon: (
      <span className="ant-icon delete-icon">
        <MdOutlineDelete fontSize={18}/>
      </span>
    ),
  },
];

type ListViewItemProps = {
  document: Document;
  name: string;
  createdAt: string;
  dropdownMenus?: ReactNode;
  onDocumentClick: (doc: Document) => void;
  activeDocument?: Document | null;
  allowSelection?: boolean;
  selectedDocs: string[];
  setSelectedDocs: (updater: (prev: string[]) => string[]) => void;
  currentSpace: { token: string };
  onDocumentEdit: (doc: Document) => void;
  onDocumentDelete: (doc: Document) => void;
};

const ListViewItem = ({
                        document,
                        name,
                        createdAt,
                        dropdownMenus,
                        onDocumentClick,
                        activeDocument,
                        allowSelection,
                        selectedDocs,
                        setSelectedDocs,
                        currentSpace,
                        onDocumentEdit,
                        onDocumentDelete,
                      }: ListViewItemProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const {formatMessage} = useIntl();

  const onEmailToggleSelect = () => {
    const documentId = document.document_id;
    if (!documentId) return;

    setSelectedDocs((prev: string[]) => {
      if (prev.includes(documentId)) {
        return prev.filter((item) => item !== documentId);
      } else {
        return [...prev, documentId];
      }
    });
  };

  const onClick = () => {
    if (allowSelection) {
      onEmailToggleSelect();
    } else {
      onDocumentClick(document);
    }
  };

  const onEditClick = (event: any) => {
    event.stopPropagation();
    const spaceToken = currentSpace?.token;
    if (!spaceToken) return;

    getDataApi(
      `knowledge_base/${spaceToken}/connector-doc-data/${document.document_id}/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        onDocumentEdit(response.data);
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err.message);
      });
  };

  const onDeleteClick = (event: any) => {
    event.stopPropagation();
    setDeleteOpen(true);
  };

  const onDeleteConfirm = () => {
    const spaceToken = currentSpace?.token;
    if (!spaceToken) return;
    setDeleteOpen(false);
    deleteDataApi(
      `knowledge_base/${spaceToken}/connector-doc-data/${document.document_id}/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        onDocumentDelete(document);
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err.message);
      });
  };

  const onMenuClick = ({key, domEvent}: any) => {
    if (key === 'edit') {
      onEditClick(domEvent);
    } else if (key === 'delete') {
      onDeleteClick(domEvent);
    }
  };

  return (
    <StyledRoot
      className={clsx('email-item', {
        active:
          !allowSelection &&
          activeDocument?.document_id === document.document_id,
        selected:
          allowSelection &&
          !!document.document_id &&
          selectedDocs.includes(document.document_id),
      })}
      onClick={onClick}
    >
      <StyledListHeader>
        <StyledMeta ellipsis>
          <StyledItem>
            <UserAvatar user={{full_name: name}}/>
          </StyledItem>
          <StyledMetaContent>
            {/*<Title
              level={5}
              className={clsx({ 'font-weight-normal': document.seen })}
              ellipsis={{ tooltip: document.title }}
            >
              {document.title}
            </Title>*/}
            <StyledItem>
              <Text>{name}</Text>
            </StyledItem>
          </StyledMetaContent>
        </StyledMeta>

        <StyledHeaderExtra>
          <Space>
            {document.seen ? null : <Badge color="#796cff"/>}

            <Tooltip
              title={changeDateStringFormat(
                createdAt,
                'YYYY-MM-DD HH:mm:ss',
                'hh:mm A . DD MMM, YYYY',
              )}
            >
              <Text type="secondary">
                {changeDateStringFormat(
                  createdAt,
                  'YYYY-MM-DD HH:mm:ss',
                  'DD MMM',
                )}
              </Text>
            </Tooltip>

            {allowSelection && (
              <Button
                type={'text'}
                shape="circle"
                size="small"
                icon={
                  document.document_id &&
                  selectedDocs.includes(document.document_id) ? (
                    <MdOutlineCheckBox fontSize={21}/>
                  ) : (
                    <MdCheckBoxOutlineBlank fontSize={21}/>
                  )
                }
              />
            )}

            {dropdownMenus}

            <Dropdown
              menu={{
                items: getLocalizedOptions(
                  menuItems,
                  formatMessage,
                ) as MenuProps['items'],
                onClick: onMenuClick,
              }}
              trigger={['click']}
            >
              <Button
                type="text"
                shape="circle"
                size="small"
                icon={<MdOutlineMoreVert fontSize={21}/>}
                onClick={(e) => e.stopPropagation()}
              />
            </Dropdown>
          </Space>
        </StyledHeaderExtra>
      </StyledListHeader>
      <StyledContent>
        <StyledContentDetails>
          <Title
            level={4}
            className={clsx({'font-weight-normal': document.seen})}
            ellipsis
          >
            {document.title}
          </Title>

          {document.description && (
            <Paragraph type="secondary" className="mb-0" ellipsis={{rows: 2}}>
              {getStringFromHtml(document.description)}
            </Paragraph>
          )}
        </StyledContentDetails>
      </StyledContent>

      <AppConfirmModal
        open={isDeleteOpen}
        onOk={onDeleteConfirm}
        message={formatMessage({id: 'spaceHeader.docsDeleteButton'})}
        onCancel={() => setDeleteOpen(false)}
      />
    </StyledRoot>
  );
};

export default ListViewItem;
