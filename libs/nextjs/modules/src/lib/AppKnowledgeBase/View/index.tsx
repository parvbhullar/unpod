'use client';
import {
  type ComponentType,
  Fragment,
  isValidElement,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  deleteDataApi,
  getDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import AppPageContainer from '@unpod/components/common/AppPageContainer';
import { Button, Dropdown, Tooltip } from 'antd';
import {
  MdArrowUpward,
  MdEdit,
  MdList,
  MdOutlineSettings,
  MdRefresh,
} from 'react-icons/md';
import { useRouter } from 'next/navigation';
import { isEditAccessAllowed } from '@unpod/helpers/PermissionHelper';
import AppTable from '@unpod/components/third-party/AppTable';
import TextEditor from './TextEditor';
import { ACCESS_ROLE } from '@unpod/constants/AppEnums';
import type { CollectionDataResponse, CollectionRecord } from '@unpod/constants/types';
import {
  capitalizedAllWords,
  convertMachineNameToName,
} from '@unpod/helpers/StringHelper';
import { AppDrawer } from '@unpod/components/antd';
import AppDotFlashing from '@unpod/components/common/AppDotFlashing';
import AppEmptyWorkSpace from '@unpod/components/modules/AppEmptyWorkSpace';
import { AppHeaderButton } from '@unpod/components/common/AppPageHeader';
import { getKbInputsStructure } from '@unpod/helpers/AppKbHelper';
import AppKbSchemaManager from '@unpod/components/modules/AppKbSchemaManager';
import AppConnectorsSetting from '@unpod/components/modules/AppConnectorsSetting';
import AppConnectorList from '@unpod/components/modules/AppConnectorList';
import AppColumnZoomView from '@unpod/components/common/AppColumnZoomView';
import AppColumnZoomCell from '@unpod/components/common/AppColumnZoomView/AppColumnZoomCell';
import { SITE_URL } from '@unpod/constants';
import PageHeader from './PageHeader';
import EditRecord from './PageHeader/EditRecord';
import HeaderDropdown from './HeaderDropdown';
import UploadDocuments from './UploadDocuments';
import Connectors from './Connectors';
import TasksView from './TasksView';
import {
  IconWrapper,
  StyledNoAccessContainer,
  StyledNoAccessText,
  StyledTableRoot,
  StyledUploadRoot,
} from './index.styled';
import { LoadingConnectorsOrUpload, LoadingTable } from '@unpod/skeleton';
import { useSkeleton } from '@unpod/custom-hooks/useSkeleton';
import { openConfirmModal } from '@unpod/helpers/ComponentHelper';
import { useIntl } from 'react-intl';

const PAGE_SIZE = 50;

const hasSameRecordIds = (
  prev: Array<Record<string, unknown>> | undefined,
  next: Array<Record<string, unknown>> | undefined,
): boolean => {
  if (prev === next) return true;
  if (!prev || !next) return false;
  if (prev.length !== next.length) return false;
  return prev.every((item, index) => item?.id === next[index]?.id);
};

const hasSameInputs = (prev: any[] | undefined, next: any[] | undefined): boolean => {
  if (prev === next) return true;
  if (!prev || !next) return false;
  if (prev.length !== next.length) return false;
  return prev.every((item, index) => {
    const other = next[index];
    return (
      item?.name === other?.name &&
      item?.title === other?.title &&
      item?.type === other?.type
    );
  });
};
const AppTableAny = AppTable as any;

type AppKnowledgeBaseModuleProps = {
  pageTitle?: any;
  knowledgeBase?: any;
};

const AppKnowledgeBaseModule = ({
  pageTitle,
  knowledgeBase,
}: AppKnowledgeBaseModuleProps) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const router = useRouter();
  const { formatMessage } = useIntl();
  const { isAuthenticated, activeOrg } = useAuthContext();

  const activeOrgRef = useRef(activeOrg?.domain_handle ?? null);
  const [currentKb, setCurrentKb] = useState(knowledgeBase);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [openTasks, setOpenTasks] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<any[]>([]);
  const [addNew, setAddNew] = useState(false);
  const [isEditOpen, setEditOpen] = useState(false);
  const [isSchemaOpen, setSchemaOpen] = useState(false);
  const [openConnectors, setOpenConnectors] = useState(false);
  const [indexLoading, setIndexLoading] = useState(false);
  const [columns, setColumns] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [inputs, setInputs] = useState<any[]>([]);
  const [records, setRecords] = useState<CollectionRecord[]>([]);
  const [isSyncing, setSyncing] = useState(false);
  const [selectedCol, setSelectedCol] = useState<any>(null);

  const { isPageLoading, skeleton: SkeletonComponent } = useSkeleton(
    LoadingTable as ComponentType<unknown>,
    LoadingConnectorsOrUpload as ComponentType<unknown>,
    `knowledge_base/${currentKb?.token}`,
  );
  const SkeletonView = isValidElement(SkeletonComponent) ? (
    SkeletonComponent
  ) : (
    <SkeletonComponent />
  );

  const [
    { apiData, loading: isLoading, isLoadingMore },
    { updateInitialUrl, setQueryParams, reCallAPI, setLoadingMore },
  ] = useGetDataApi<CollectionDataResponse>(
    `knowledge_base/${knowledgeBase?.token}/collection-data/`,
    { data: { data: [], schemas: undefined, count: 0 } },
    { page: 1, page_size: PAGE_SIZE },
    false,
  );

  useEffect(() => {
    if (!activeOrgRef.current) {
      activeOrgRef.current = activeOrg?.domain_handle ?? null;
    } else if (
      activeOrgRef.current &&
      activeOrgRef.current !== activeOrg?.domain_handle
    ) {
      activeOrgRef.current = activeOrg?.domain_handle ?? null;
      router.push('/knowledge-bases/');
    }
  }, [activeOrg?.domain_handle]);

  const { items, connector } = useMemo(() => {
    const [connector] = currentKb?.connected_apps || [];

    const options: Array<{
      key: string;
      label: string;
      icon: JSX.Element;
      disabled?: boolean;
    }> = [
      {
        key: 'index',
        label: 'knowledgeBase.index',
        disabled: !(selectedRowKeys.length > 0) || indexLoading,
        icon: (
          <span className="ant-icon">
            <MdOutlineSettings fontSize={16} />
          </span>
        ),
      },
    ];

    if (isEditAccessAllowed(undefined, undefined, currentKb)) {
      options.push({
        key: 'edit_kb',
        label: 'common.edit',
        icon: (
          <span className="ant-icon">
            <MdEdit fontSize={16} />
          </span>
        ),
      });

      if (currentKb?.content_type === 'contact') {
        options.push({
          key: 'tasks',
          label: 'Tasks',
          icon: (
            <span className="ant-icon">
              <MdList fontSize={18} />
            </span>
          ),
        });
      }

      if (!connector && currentKb?.content_type !== 'email') {
        options.push({
          key: 'upload',
          label: 'knowledgeBase.upload',
          icon: (
            <span className="ant-icon">
              <MdArrowUpward fontSize={16} />
            </span>
          ),
        });

        options.push({
          key: 'edit_schema',
          label: 'knowledgeBase.editSchema',
          icon: (
            <span className="ant-icon">
              <MdEdit fontSize={16} />
            </span>
          ),
        });
        /* options.push({//TODO remove this add update edit api
          key: 'delete_kb',
          label: (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                color: '#ff4d4f',
              }}
            >
              <MdDelete fontSize={16} />
              <span style={{ marginLeft: 8, color: '#ff4d4f' }}>Delete</span>
            </span>
          ),
        });*/
      }
    }

    return { items: options, connector };
  }, [selectedRowKeys, currentKb, indexLoading]);

  useEffect(() => {
    if (knowledgeBase && isAuthenticated) {
      setCurrentKb(knowledgeBase);
    }
  }, [knowledgeBase, isAuthenticated]);

  const getSyncStatus = useCallback(() => {
    if (currentKb?.token) {
      getDataApi(
        `knowledge_base/${currentKb?.token}/upload-status/`,
        infoViewActionsContext,
      )
        .then((response: any) => {
          if (response.data.indexing > 0) {
            setSyncing(true);

            setTimeout(() => {
              getSyncStatus();
            }, 1000 * 30);
          } else {
            setSyncing(false);
          }
        })
        .catch((error) => {
          if (error?.error) {
            infoViewActionsContext.showError(error.error);
          } else {
            infoViewActionsContext.showError(error.message);
          }
        });
    }
  }, [currentKb?.token]);

  useEffect(() => {
    const token = currentKb?.token;
    if (token && isAuthenticated) {
      setRecords([]);
      setColumns([]);
      setPage(1);

      if (currentKb?.final_role !== ACCESS_ROLE.GUEST) {
        updateInitialUrl(`knowledge_base/${token}/collection-data/`);
        getSyncStatus();
      }
    }
  }, [currentKb?.token, isAuthenticated]);

  useEffect(() => {
    if (
      currentKb?.token &&
      currentKb?.final_role !== ACCESS_ROLE.GUEST &&
      isAuthenticated
    ) {
      setQueryParams({ page: page, page_size: PAGE_SIZE });
    }
  }, [page, currentKb?.token, isAuthenticated]);

  useEffect(() => {
    const responseData = apiData?.data;
    if (responseData) {
      if (page === 1) {
        setRecords((prevData) =>
          hasSameRecordIds(prevData, responseData.data)
            ? prevData
            : responseData.data,
        );
      } else {
        setRecords((prevData) => {
          if (!responseData.data?.length) {
            return prevData;
          }
          const combined = [...prevData, ...responseData.data];
          return hasSameRecordIds(prevData, combined) ? prevData : combined;
        });
      }

      const schema = responseData.schemas || { properties: undefined };
      if (schema.properties) {
        const formInputs = getKbInputsStructure(schema);
        setInputs((prevInputs) =>
          hasSameInputs(prevInputs, formInputs) ? prevInputs : formInputs,
        );
      }
    }
  }, [apiData, page]);

  useEffect(() => {
    setColumns(
      inputs.map((input: any) => {
        const title = capitalizedAllWords(
          convertMachineNameToName(input.title) || '',
        );
        const columnKey = input.name || input.title || '';

        return {
          title: title,
          dataIndex: columnKey,
          key: columnKey,
          dataType: input.type,
          sorter: (a: any, b: any) => a[columnKey] - b[columnKey],
          render: (value: any) => (
            <AppColumnZoomCell
              title={title}
              value={value}
              setSelectedCol={setSelectedCol}
            />
          ),
          renderEditCell: TextEditor,
          headerCellOptions: true,
        };
      }),
    );
  }, [inputs]);

  const onRenameColumn = (columnKey: string, newTitle: string) => {
    const updatedColumns = columns.map((column: any) => {
      if (column.dataIndex === columnKey) {
        return { ...column, title: newTitle };
      }
      return column;
    });

    setColumns(updatedColumns);
  };

  const indexRecords = () => {
    setIndexLoading(true);
    getDataApi(
      `knowledge_base/${currentKb?.token}/index/`,
      infoViewActionsContext,
      {
        token: selectedRowKeys.toString(),
      },
    )
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setIndexLoading(false);
        setSelectedRowKeys([]);
      })
      .catch((error: any) => {
        setIndexLoading(false);
        infoViewActionsContext.showError(error.message);
      });
  };

  const onMenuClick = (item: { key: string }) => {
    if (item.key === 'edit_kb') {
      setEditOpen(true);
    } else if (item.key === 'edit_schema') {
      setSchemaOpen(true);
    } else if (item.key === 'upload') {
      setIsModalOpen(true);
    } else if (item.key === 'index') {
      indexRecords();
    } else if (item.key === 'tasks') {
      setOpenTasks(true);
    } else if (item.key === 'delete_kb') {
      openConfirmModal(
        {
          content: formatMessage({ id: 'identityStudio.deleteConfirm' }),
          onOk: onDelete,
        },
        formatMessage,
      );
    }
  };
  const onDelete = () => {
    deleteDataApi(`knowledge_base/${currentKb?.token}/`, infoViewActionsContext)
      .then((response: any) => {
        infoViewActionsContext.showMessage(response.message);
        setCurrentKb(null);
        setRecords([]);
        setColumns([]);
        setSelectedRowKeys([]);
        router.push(`/knowledge-bases/`);
      })
      .catch((error: any) => {
        infoViewActionsContext.showError(error.message);
      });
  };

  const onScrolledToBottom = () => {
    if (records.length > 0 && records.length === page * PAGE_SIZE) {
      const nextPage = page + 1;
      setLoadingMore(true);
      setPage(nextPage);
    }
  };

  const onRefreshClick = () => {
    getDataApi(
      `knowledge_base/${currentKb?.token}/upload-status/`,
      infoViewActionsContext,
    )
      .then((response: any) => {
        if (response.data.indexing > 0) {
          setSyncing(true);
        } else {
          setSyncing(false);
        }
      })
      .catch((error) => {
        if (error?.error) {
          infoViewActionsContext.showError(error.error);
        } else {
          infoViewActionsContext.showError(error.message);
        }
      });
  };

  return (
    <Fragment>
      <PageHeader
        pageTitle={pageTitle}
        dropdownMenu={
          <HeaderDropdown
            pageTitle={pageTitle}
            currentKb={currentKb}
            setCurrentKb={setCurrentKb}
            addNew={addNew}
            setAddNew={setAddNew}
          />
        }
        currentKb={currentKb}
        setCurrentKb={setCurrentKb}
        documents={records}
        selectedRowKeys={selectedRowKeys}
        setSelectedRowKeys={setSelectedRowKeys}
        rightOptions={
          currentKb &&
          currentKb?.final_role !== ACCESS_ROLE.GUEST && (
            <Fragment>
              {/*  {selectedRowKeys.length > 0 && ( //TODO remove this add update edit api
                <AppHeaderButton
                  type="primary"
                  shape="round"
                  icon={<MdDelete fontSize={16} />}
                  onClick={onDeleteSeleceted}
                >
                  Delete
                </AppHeaderButton>
              )}*/}
              {connector ? (
                <AppConnectorsSetting data={currentKb} setData={setCurrentKb} />
              ) : (
                isEditAccessAllowed(undefined, undefined, currentKb) && (
                  <Tooltip
                    title={
                      isSyncing
                        ? formatMessage({ id: 'knowledgeBase.clickToRefresh' })
                        : ''
                    }
                  >
                    <AppHeaderButton
                      type="primary"
                      shape="round"
                      onClick={() =>
                        isSyncing ? onRefreshClick() : setOpenConnectors(true)
                      }
                      ghost
                    >
                      {isSyncing
                        ? formatMessage({ id: 'knowledgeBase.syncing' })
                        : currentKb?.content_type === 'email'
                          ? formatMessage({ id: 'common.connect' })
                          : formatMessage({ id: 'knowledgeBase.import' })}

                      {isSyncing && (
                        <AppDotFlashing
                          style={{ display: 'flex', marginLeft: 0, width: 28 }}
                        />
                      )}

                      {isSyncing && <MdRefresh fontSize={18} />}
                    </AppHeaderButton>
                  </Tooltip>
                )
              )}
              <Dropdown
                menu={{
                  items: items.map((item) => ({
                    ...item,
                    label: formatMessage({ id: item.label }),
                  })),
                  onClick: onMenuClick,
                }}
                placement="bottomRight"
                trigger={['click']}
              >
                <IconWrapper>
                  <MdOutlineSettings fontSize={24} />
                </IconWrapper>
              </Dropdown>
            </Fragment>
          )
        }
      />

      <AppPageContainer style={{ position: 'relative' }}>
        {currentKb?.final_role === ACCESS_ROLE.GUEST ? (
          <StyledNoAccessContainer>
            <StyledNoAccessText level={2}>
              {formatMessage({ id: 'knowledgeBase.noAccess' })}
            </StyledNoAccessText>
          </StyledNoAccessContainer>
        ) : (
          <>
            {records?.length > 0 ? (
              <StyledTableRoot>
                {isPageLoading ? (
                  SkeletonView
                ) : (
                  <AppTableAny
                    rowKey="id"
                    isLoadingMore={isLoadingMore}
                    rowSelection={{
                      type: 'checkbox',
                      onChange: (selectedRowKeys: any[]) => {
                        setSelectedRowKeys(selectedRowKeys);
                      },
                      selectedRowKeys,
                    }}
                    loading={isLoading}
                    columns={columns}
                    dataSource={records}
                    size="middle"
                    pagination={false}
                    onScrolledToBottom={onScrolledToBottom}
                    allowGridActions
                    configuration={{
                      showSerialNoRow: false,
                      allowEditorToolbar: false,
                      allowCountFooter: false,
                      allowFormula: false,
                    }}
                    onRenameColumn={onRenameColumn}
                  />
                )}
              </StyledTableRoot>
            ) : (
              !isLoading &&
              (currentKb &&
              isEditAccessAllowed(undefined, undefined, currentKb) ? (
                <StyledUploadRoot>
                  {currentKb?.content_type === 'email' ? (
                    <Connectors
                      currentKb={currentKb}
                      connector={connector}
                      setOpenConnectors={setOpenConnectors}
                    />
                  ) : (
                    <UploadDocuments
                      currentKb={currentKb}
                      onSaved={() => {
                        reCallAPI();
                        getSyncStatus();
                      }}
                    />
                  )}
                </StyledUploadRoot>
              ) : (
                <AppEmptyWorkSpace type="kb">
                  <Button type="primary" onClick={() => setAddNew(true)}>
                    {formatMessage({ id: 'knowledgeBase.addKnowledgeBase' })}
                  </Button>
                </AppEmptyWorkSpace>
              ))
            )}
          </>
        )}
      </AppPageContainer>

      <AppDrawer
        title={
          currentKb?.content_type === 'email'
            ? formatMessage({ id: 'common.connect' })
            : formatMessage({ id: 'knowledgeBase.import' })
        }
        open={openConnectors}
        onClose={() => setOpenConnectors(false)}
        size={560}
      >
        {openConnectors && currentKb && (
          <Fragment>
            {currentKb?.content_type === 'email' ? (
              <AppConnectorList
                defaultPayload={{
                  redirect_route: `${SITE_URL}/knowledge-bases/${currentKb.slug}/`,
                  kb: currentKb.slug,
                }}
              />
            ) : (
              <UploadDocuments
                currentKb={currentKb}
                onSaved={() => {
                  reCallAPI();
                  setOpenConnectors(false);
                  getSyncStatus();
                }}
              />
            )}
          </Fragment>
        )}
      </AppDrawer>

      <AppDrawer
        title={formatMessage({ id: 'knowledgeBase.uploadFiles' })}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        size={560}
      >
        {isModalOpen && (
          <UploadDocuments
            currentKb={currentKb}
            onSaved={() => {
              reCallAPI();
              setIsModalOpen(false);
              getSyncStatus();
            }}
          />
        )}
      </AppDrawer>

      <AppDrawer
        title={formatMessage({ id: 'knowledgeBase.updateKnowledgeBase' })}
        open={isEditOpen}
        destroyOnHidden={true}
        onClose={() => setEditOpen(false)}
        size={560}
      >
        {isEditOpen && (
          <EditRecord
            currentKb={currentKb}
            setCurrentKb={setCurrentKb}
            onClose={() => setEditOpen(false)}
          />
        )}
      </AppDrawer>

      <AppDrawer
        title={formatMessage({ id: 'knowledgeBase.manageSchema' })}
        open={isSchemaOpen}
        destroyOnHidden={true}
        onClose={() => setSchemaOpen(false)}
        size={720}
      >
        {isSchemaOpen && (
          <AppKbSchemaManager
            title={formatMessage({ id: 'knowledgeBase.schema' })}
            currentKb={currentKb}
            inputs={inputs}
            setInputs={setInputs}
            onClose={() => setSchemaOpen(false)}
          />
        )}
      </AppDrawer>

      <AppDrawer
        title={selectedCol?.title}
        open={selectedCol !== null}
        destroyOnHidden={true}
        onClose={() => setSelectedCol(null)}
        styles={{ body: { padding: 0, position: 'relative' } }}
        width="60%"
      >
        <AppColumnZoomView selectedCol={selectedCol} />
      </AppDrawer>

      <AppDrawer
        title={formatMessage({ id: 'knowledgeBase.tasks' })}
        open={openTasks}
        destroyOnHidden={true}
        onClose={() => setOpenTasks(false)}
        styles={{ body: { padding: 0, position: 'relative' } }}
        width="80%"
      >
        <TasksView currentKb={currentKb} />
      </AppDrawer>
    </Fragment>
  );
};

export default AppKnowledgeBaseModule;
