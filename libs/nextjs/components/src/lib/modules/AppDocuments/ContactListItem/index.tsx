
import { Typography } from 'antd';
import clsx from 'clsx';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import UserAvatar from '../../../common/UserAvatar';
import {
  StyledInnerRoot,
  StyledItem,
  StyledListHeader,
  StyledMeta,
  StyledParagraph,
  StyledRoot,
} from './index.styled';
import { useRouter } from 'next/navigation';
import { IoCallOutline } from 'react-icons/io5';

const { Title } = Typography;

type ContactDocument = {
  document_id: string;
  name: string;
  seen?: boolean;
  [key: string]: any;
};

type ContactListItemProps = {
  data: ContactDocument;
  showTimeFrom?: boolean;};

const ContactListItem = ({ data }: ContactListItemProps) => {
  const { setActiveDocument, setDocumentMode, setSelectedDocs } =
    useAppSpaceActionsContext();
  const { activeDocument, activeTab, currentSpace, selectedDocs } =
    useAppSpaceContext();

  const allowSelection = activeTab === 'logs';
  const router = useRouter();

  const onDocumentClick = (doc: ContactDocument) => {
    if (!currentSpace?.slug) {
      return;
    }
    // if (!activeDocument) setActiveTab('doc');
    setActiveDocument(doc);
    setSelectedDocs([doc.document_id]);
    // updateBreadcrumb(doc.title);
    router.replace(
      `/spaces/${currentSpace.slug}/${activeTab}/${doc.document_id}`,
    );
  };

  // const onDocumentDelete = (doc) => {
  //   connectorActions.setData(
  //     connectorData.apiData.filter(
  //       (item) => item.document_id !== doc.document_id
  //     )
  //   );
  //
  //   if (activeDocument?.document_id === doc.document_id || !activeDocument)
  //     setActiveDocument(null);
  // };

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
      setDocumentMode('view');
    }
  };

  // const onEditClick = () => {
  //   getDataApi(
  //     `knowledge_base/${currentSpace.token}/connector-doc-data/${data.document_id}/`,
  //     infoViewActionsContext
  //   )
  //     .then((response) => {
  //       setActiveDocument(response.data);
  //       setDocumentMode('edit');
  //     })
  //     .catch((err) => {
  //       infoViewActionsContext.showError(err.message);
  //     });
  // };

  // const onDeleteClick = () => {
  //   setDeleteOpen(true);
  // };

  // const onDeleteConfirm = () => {
  //   setDeleteOpen(false);
  //   onDocumentDelete(data);
  //   deleteDataApi(
  //     `knowledge_base/${currentSpace.token}/connector-doc-data/${data.document_id}/`,
  //     infoViewActionsContext
  //   )
  //     .then((response) => {
  //       onDocumentDelete(data);
  //       infoViewActionsContext.showMessage(response.message);
  //     })
  //     .catch((err) => {
  //       infoViewActionsContext.showError(err.message);
  //     });
  // };

  // const onMenuClick = ({ key, domEvent }) => {
  //   domEvent.stopPropagation();
  //   if (key === 'edit') {
  //     onEditClick(domEvent);
  //   } else if (key === 'delete') {
  //     onDeleteClick(domEvent);
  //   }
  // };

  return (
    <>
      <StyledRoot
        className={clsx('email-item', {
          active:
            !allowSelection && activeDocument?.document_id === data.document_id,
          selected: allowSelection && selectedDocs.includes(data.document_id),
        })}
        onClick={onClick}
      >
        <StyledItem>
          <UserAvatar user={{ full_name: data.name }} size={36} />
        </StyledItem>

        <StyledInnerRoot>
          <StyledListHeader>
            <StyledMeta>
              <Title
                level={5}
                className={clsx({
                  'font-weight-normal': data.seen,
                })}
                ellipsis
              >
                {data.name}
              </Title>
            </StyledMeta>

            {/*<StyledHeaderExtra>*/}
            {/*  <Space>*/}
            {/*    {data.seen ? null : <Badge color="#796cff" />}*/}

            {/*    <Tooltip*/}
            {/*      title={changeDateStringFormat(*/}
            {/*        data.created,*/}
            {/*        'YYYY-MM-DD HH:mm:ss',*/}
            {/*        'hh:mm A . DD MMM, YYYY'*/}
            {/*      )}*/}
            {/*    >*/}
            {/*      <Text type="secondary">*/}
            {/*        {showTimeFrom*/}
            {/*          ? getTimeFromNow(data.created)*/}
            {/*          : changeDateStringFormat(*/}
            {/*              data.created,*/}
            {/*              'YYYY-MM-DD HH:mm:ss',*/}
            {/*              'DD MMM'*/}
            {/*            )}*/}
            {/*      </Text>*/}
            {/*    </Tooltip>*/}

            {/*    {allowSelection && (*/}
            {/*      <Button*/}
            {/*        type={'text'}*/}
            {/*        shape="circle"*/}
            {/*        size="small"*/}
            {/*        icon={*/}
            {/*          selectedDocs.includes(data.document_id) ? (*/}
            {/*            <MdOutlineCheckBox fontSize={21} />*/}
            {/*          ) : (*/}
            {/*            <MdCheckBoxOutlineBlank fontSize={21} />*/}
            {/*          )*/}
            {/*        }*/}
            {/*      />*/}
            {/*    )}*/}

            {/*    <Dropdown*/}
            {/*      menu={{ items: menuItems, onClick: onMenuClick }}*/}
            {/*      trigger={['click']}*/}
            {/*      onClick={(e) => {*/}
            {/*        e.stopPropagation();*/}
            {/*      }}*/}
            {/*    >*/}
            {/*      <Button*/}
            {/*        type="text"*/}
            {/*        shape="circle"*/}
            {/*        size="small"*/}
            {/*        icon={<MdOutlineMoreVert fontSize={21} />}*/}
            {/*      />*/}
            {/*    </Dropdown>*/}
            {/*  </Space>*/}
            {/*</StyledHeaderExtra>*/}
          </StyledListHeader>

          {data.name && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                marginTop: -6,
              }}
            >
              <IoCallOutline size={12} />
              <StyledParagraph type="secondary" className="mb-0" ellipsis>
                {data.contact_number || data.title}
              </StyledParagraph>
            </div>
          )}
        </StyledInnerRoot>
      </StyledRoot>

      {/*<AppConfirmModal*/}
      {/*  open={isDeleteOpen}*/}
      {/*  onOk={onDeleteConfirm}*/}
      {/*  message="Are you sure you want to delete this document?"*/}
      {/*  onCancel={() => setDeleteOpen(false)}*/}
      {/*/>*/}
    </>
  );
};

export default ContactListItem;
