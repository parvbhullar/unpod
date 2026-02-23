import {useState} from 'react';

import type {MenuProps} from 'antd';
import {Badge, Button, Dropdown, Space, Tooltip, Typography} from 'antd';
import {MdCheckBoxOutlineBlank, MdOutlineCheckBox, MdOutlineDelete, MdOutlineMoreVert,} from 'react-icons/md';
import clsx from 'clsx';
import {changeDateStringFormat, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import {
  deleteDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import UserAvatar from '../../../common/UserAvatar';
import {
  StyledHeaderExtra,
  StyledInnerRoot,
  StyledItem,
  StyledListHeader,
  StyledMeta,
  StyledRoot,
} from './index.styled';
import AppConfirmModal from '../../../antd/AppConfirmModal';
import {useRouter} from 'next/navigation';
import {useIntl} from 'react-intl';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';

const {Paragraph, Title, Text} = Typography;

const menuItems = [
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

type GeneralDocument = {
  document_id: string;
  title: string;
  description?: string;
  content?: string;
  name?: string;
  seen?: boolean;
  created?: string;
  [key: string]: any;
};

type GeneralListItemProps = {
  data: GeneralDocument;
  showTimeFrom?: boolean;
};

const GeneralListItem = ({data, showTimeFrom}: GeneralListItemProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const {setActiveDocument, setBreadcrumb, setActiveTab, setSelectedDocs} =
    useAppSpaceActionsContext();
  const {activeDocument, activeTab, currentSpace, selectedDocs} =
    useAppSpaceContext();
  const allowSelection = activeTab === 'logs';
  const router = useRouter();
  const {formatMessage} = useIntl();

  const onDocumentClick = (doc: GeneralDocument) => {
    if (!currentSpace?.slug) return;
    if (!activeDocument) setActiveTab('knowledge');
    router.replace(
      `/spaces/${currentSpace.slug}/${activeTab}/${doc.document_id}`,
    );
    setActiveDocument(doc);
    setBreadcrumb(doc.title);
  };

  const onDocumentDelete = (_doc: GeneralDocument) => {
    // setRecords((prevData) =>
    //   prevData.filter((item) => item.document_id !== doc.document_id)
    // );
    // newSourceRef.current.deleteDocument();
  };

  const onEmailToggleSelect = () => {
    setSelectedDocs((prev: any[]) => {
      if (prev.includes(data.document_id)) {
        return prev.filter((item) => item !== data.document_id);
      } else {
        return [...prev, data.document_id];
      }
    });
  };

  const onClick = () => {
    if (allowSelection) {
      onEmailToggleSelect();
    } else {
      onDocumentClick(data);
    }
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
      `knowledge_base/${spaceToken}/connector-doc-data/${data.document_id}/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        onDocumentDelete(data);
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err.message);
      });
  };

  const onMenuClick = ({key, domEvent}: any) => {
    if (key === 'delete') {
      onDeleteClick(domEvent);
    }
  };

  return (
    <StyledRoot
      className={clsx('email-item', {
        active:
          !allowSelection && activeDocument?.document_id === data.document_id,
        selected: allowSelection && selectedDocs.includes(data.document_id),
      })}
      onClick={onClick}
    >
      <StyledItem>
        <UserAvatar user={{full_name: data.name}} size={36}/>
      </StyledItem>

      <StyledInnerRoot>
        <StyledListHeader>
          <StyledMeta>
            <Title
              level={5}
              className={clsx({'font-weight-normal': data.seen})}
              ellipsis
            >
              {data.title}
            </Title>
          </StyledMeta>

          <StyledHeaderExtra>
            <Space>
              {data.seen ? null : <Badge color="#796cff"/>}

              {data.created && (
                <Tooltip
                  title={changeDateStringFormat(
                    data.created,
                    'YYYY-MM-DD HH:mm:ss',
                    'hh:mm A . DD MMM, YYYY',
                  )}
                >
                  <Text type="secondary">
                    {showTimeFrom
                      ? getTimeFromNow(data.created)
                      : changeDateStringFormat(
                        data.created,
                        'YYYY-MM-DD HH:mm:ss',
                        'DD MMM',
                      )}
                  </Text>
                </Tooltip>
              )}

              {allowSelection && (
                <Button
                  type={'text'}
                  shape="circle"
                  size="small"
                  icon={
                    selectedDocs.includes(data.document_id) ? (
                      <MdOutlineCheckBox fontSize={21}/>
                    ) : (
                      <MdCheckBoxOutlineBlank fontSize={21}/>
                    )
                  }
                />
              )}

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

        {(data.description || data.content) && (
          <Paragraph
            type="secondary"
            className="mb-0"
            style={{maxWidth: '90%'}}
            ellipsis
          >
            {getStringFromHtml(data.description || data.content)}
          </Paragraph>
        )}
      </StyledInnerRoot>

      <AppConfirmModal
        open={isDeleteOpen}
        onOk={onDeleteConfirm}
        message={formatMessage({id: 'spaceHeader.docsDeleteButton'})}
        onCancel={() => setDeleteOpen(false)}
      />
    </StyledRoot>
  );
};

export default GeneralListItem;
