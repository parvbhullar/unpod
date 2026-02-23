'use client';
import {Fragment, useState} from 'react';
import {MdCall, MdOutlineDelete, MdOutlineEdit, MdOutlineMoreVert, MdRefresh,} from 'react-icons/md';
import {
  deleteDataApi,
  getDataApi,
  useAppSpaceActionsContext,
  useAppSpaceContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import ExportTasks from './ExportTasks';
import {AppHeaderButton} from '../../common/AppPageHeader';
import AppSpaceCallModal from './AppSpaceCallModal';
import type {MenuProps} from 'antd';
import {Dropdown} from 'antd';
import AppConfirmModal from '../../antd/AppConfirmModal';
import {AppDrawer, DrawerBody} from '../../antd';
import {useMediaQuery} from 'react-responsive';
import {MobileWidthQuery} from '@unpod/constants';
import {useIntl} from 'react-intl';
import {getLocalizedOptions} from '@unpod/helpers/LocalizationFormatHelper';

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

type AppSpaceContactCallProps = {
  selectedRowKeys?: Array<string | number>;
  idKey?: string;
  onFinishSchedule?: (data: any) => void;
  onRefreshTasks?: () => void;
  data?: any;
  hideExport?: boolean;
  type?: string;
  drawerChildren?: React.ReactNode;
};

const AppSpaceContactCall = ({
                               selectedRowKeys,
                               idKey = 'id',
                               onFinishSchedule,
                               onRefreshTasks,
                               data,
                               hideExport = false,
                               type,
                               drawerChildren
                             }: AppSpaceContactCallProps) => {
  const [isDeleteOpen, setDeleteOpen] = useState(false);
  const {connectorData, activeDocument, selectedDocs, currentSpace} =
    useAppSpaceContext();
  const mobileScreen = useMediaQuery(MobileWidthQuery);
  const infoViewActionsContext = useInfoViewActionsContext();
  const {setActiveDocument, setDocumentMode, connectorActions} =
    useAppSpaceActionsContext();
  const {formatMessage} = useIntl();

  const [open, setOpen] = useState(false);
  const [visible, setVisible] = useState(false);

  const isDisabled = () => {
    if (selectedDocs && !selectedRowKeys) {
      return !selectedDocs?.length;
    } else if (!selectedDocs && selectedRowKeys && activeDocument) {
      return !selectedRowKeys?.length;
    }
    return true;
  };

  const onDocumentDelete = (doc: any) => {
    connectorActions.setData(
      connectorData.apiData.filter(
        (item: any) => item.document_id !== doc.document_id,
      ),
    );

    if (activeDocument?.document_id === doc.document_id || !activeDocument)
      setActiveDocument(null);
  };

  const onDeleteConfirm = () => {
    setDeleteOpen(false);
    onDocumentDelete(data);
    deleteDataApi(
      `knowledge_base/${currentSpace!.token}/connector-doc-data/${data.document_id}/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        // onDocumentDelete(data);
        infoViewActionsContext.showMessage(response.message);
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err.message);
      });
  };

  const onEditClick = () => {
    getDataApi(
      `knowledge_base/${currentSpace!.token}/connector-doc-data/${data.document_id}/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        setActiveDocument(response.data);
        setDocumentMode('edit');
      })
      .catch((err: any) => {
        infoViewActionsContext.showError(err.message);
      });
  };

  const onDeleteClick = () => {
    setDeleteOpen(true);
  };

  const onMenuClick: MenuProps['onClick'] = ({key}) => {
    if (key === 'edit') {
      onEditClick();
    } else if (key === 'delete') {
      onDeleteClick();
    }
  };

  return (
    <Fragment>
      <AppHeaderButton
        type="primary"
        shape={!mobileScreen ? 'round' : 'circle'}
        icon={
          <span className="anticon" style={{verticalAlign: 'middle'}}>
            <MdCall fontSize={!mobileScreen ? 16 : 22}/>
          </span>
        }
        disabled={type === 'doc' && isDisabled()}
        onClick={() => (type === 'doc' ? setVisible(true) : setOpen(true))}
      >
        {!mobileScreen && formatMessage({id: 'spaceHeader.call'})}
      </AppHeaderButton>

      {!hideExport && <ExportTasks currentSpace={currentSpace!}/>}

      {onRefreshTasks && (
        <AppHeaderButton
          type="default"
          shape="circle"
          size="small"
          icon={<MdRefresh fontSize={20}/>}
          onClick={onRefreshTasks}
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
        <AppHeaderButton
          disabled={isDisabled()}
          shape="circle"
          size="small"
          icon={<MdOutlineMoreVert fontSize={21}/>}
        />
      </Dropdown>

      <AppConfirmModal
        open={isDeleteOpen}
        onOk={onDeleteConfirm}
        message={formatMessage({id: 'spaceHeader.docsDeleteButton'})}
        onCancel={() => setDeleteOpen(false)}
      />
      <AppDrawer
        isCallFilterView={true}
        open={open}
        onClose={() => setOpen(false)}
        closable={false}
        title={formatMessage({id: 'spaceHeader.call'})}
        extra={
          <AppHeaderButton
            type="primary"
            shape={!mobileScreen ? 'round' : 'circle'}
            icon={
              <span className="anticon" style={{verticalAlign: 'middle'}}>
                <MdCall fontSize={!mobileScreen ? 16 : 22}/>
              </span>
            }
            onClick={() => setVisible(true)}
            disabled={isDisabled()}
          >
            {!mobileScreen && formatMessage({id: 'spaceHeader.callNow'})}
          </AppHeaderButton>
        }
      >
        <DrawerBody
          $overFlowY="hidden"
          $bodyHeight={65}
          style={{overflow: 'visible', padding: '0 0 0 0'}}
        >
          {drawerChildren}
        </DrawerBody>
      </AppDrawer>

      <AppSpaceCallModal
        open={visible}
        setOpen={setVisible}
        idKey={idKey || 'id'}
        onFinishSchedule={onFinishSchedule}
      />
    </Fragment>
  );
};

export default AppSpaceContactCall;
