import {Fragment, useEffect, useState} from 'react';
import {Badge, Button, Dropdown, Tooltip} from 'antd';
import {
  MdAdd,
  MdOutlineCheckBox,
  MdOutlineCheckBoxOutlineBlank,
  MdOutlineFilterList,
  MdOutlineIndeterminateCheckBox,
  MdOutlineLabel,
  MdOutlineMoreVert,
  MdPhoneForwarded,
  MdRefresh,
} from 'react-icons/md';
import {AppDrawer} from '@unpod/components/antd';
import {useAppSpaceActionsContext, useAppSpaceContext, useGetDataApi,} from '@unpod/providers';
import ManageLabels from './ManageLabels';
import SearchBox from './SearchBox';
import {StyledContent, StyledFilterContent, StyledRoot, StyledSpace,} from './index.styled';
import {clsx} from 'clsx';
import FilterForm from './FilterForm';
import AppSpaceCallModal from '@unpod/components/modules/AppSpaceContactCall/AppSpaceCallModal';
import {cleanObject} from '@unpod/helpers/GlobalHelper';
import {useIntl} from 'react-intl';

type FormatMessage = (descriptor: { id: string }) => string;

type CurrentSpace = {
  content_type?: string;
  slug?: string;
  token?: string;
} | null;

const getLabel = (currentSpace: CurrentSpace, formatMessage: FormatMessage) => {
  if (currentSpace?.content_type === 'contact') {
    return formatMessage({id: 'peopleSidebarMenu.addContact'});
  } else if (currentSpace?.content_type === 'conversation') {
    return formatMessage({id: 'peopleSidebarMenu.addConversation'});
  } else if (currentSpace?.content_type === 'note') {
    return formatMessage({id: 'peopleSidebarMenu.addNote'});
  }
  return formatMessage({id: 'peopleSidebarMenu.addDocument'});
};

const getMenuItems = (
  currentSpace: CurrentSpace,
  filters: Record<string, any>,
  formatMessage: FormatMessage,
) => {
  const menuItems = [
    {
      key: 'refresh',
      label: formatMessage({id: 'common.refresh'}),
      icon: (
        <span className="ant-icon edit-icon">
          <MdRefresh fontSize={18}/>
        </span>
      ),
    },
    {
      key: 'add-doc',
      label: getLabel(currentSpace, formatMessage),
      icon: (
        <span className="ant-icon edit-icon">
          <MdAdd fontSize={18}/>
        </span>
      ),
    },
    {
      key: 'labels',
      label: formatMessage({id: 'peopleSidebarMenu.manageLabels'}),
      icon: (
        <span className="ant-icon edit-icon">
          <MdOutlineLabel fontSize={18}/>
        </span>
      ),
    },
  ];

  const hasFilters =
    filters && Object.keys(cleanObject(filters) || {}).length > 0;

  if (hasFilters) {
    menuItems.unshift({
      key: 'call-filtered',
      label: formatMessage({id: 'peopleSidebarMenu.callFiltered'}),
      icon: (
        <span className="ant-icon edit-icon">
          <MdPhoneForwarded fontSize={18}/>
        </span>
      ),
    });
  }

  return menuItems;
};

type SubHeaderProps = {
  isDocsLoading: boolean;
  onToggleCheck: () => void;
  checkedType: 'all' | 'none' | 'partial';
  search: string;
  setSearch: (value: string) => void;
  filters: Record<string, any>;
  allowSelection: boolean;
  setFilters: (value: Record<string, any>) => void;
};

const SubHeader = ({
                     isDocsLoading,
                     onToggleCheck,
                     checkedType,
                     search,
                     setSearch,
                     filters,
                     allowSelection,
                     setFilters,
                   }: SubHeaderProps) => {
  const {connectorActions, setActiveDocument, setDocumentMode} =
    useAppSpaceActionsContext();
  const {formatMessage} = useIntl();

  const {activeTab, currentSpace} = useAppSpaceContext();

  const [openFilter, setOpenFilter] = useState(false);
  const [open, setOpen] = useState(false);
  const [openCallScheduler, setOpenCallScheduler] = useState(false);
  const DropdownAny = Dropdown as any;

  const [{apiData, loading}, {reCallAPI, setQueryParams}] = useGetDataApi(
    `core/relevant-tags/`,
    {data: []},
    {
      content_type_model: 'space',
      slug: currentSpace?.slug,
    },
    false,
  ) as any;

  useEffect(() => {
    setQueryParams({
      content_type_model: 'space',
      slug: currentSpace?.slug,
    });
  }, [currentSpace?.slug]);

  const onApplyFilters = (appliedFilters: Record<string, any> | null) => {
    setFilters(appliedFilters || {});
    setOpenFilter(false);
  };

  const onMenuClick = ({key}: { key: string }) => {
    if (key === 'labels') {
      setOpen(true);
    } else if (key === 'refresh') {
      connectorActions.setQueryParams({page: 1});
    } else if (key === 'add-doc') {
      setDocumentMode('add');
      setActiveDocument(null);
    } else if (key === 'call-filtered') {
      setOpenCallScheduler(true);
    }
  };

  const tags = (apiData?.default_tags || []).concat(apiData?.object_tags || []);
  // count={connectorData?.count || 0}
  return (
    <Fragment>
      <StyledRoot>
        <StyledContent>
          <SearchBox
            search={search}
            setSearch={setSearch}
            currentSpace={currentSpace ?? {}}
            searchCount={0}
            loading={isDocsLoading}
          />
        </StyledContent>

        {(activeTab === 'call' || allowSelection) && (
          <Tooltip title={formatMessage({id: 'common.selectAll'})}>
            <Button
              type="text"
              shape="circle"
              size="small"
              icon={
                checkedType === 'all' ? (
                  <MdOutlineCheckBox fontSize={21}/>
                ) : checkedType === 'none' ? (
                  <MdOutlineCheckBoxOutlineBlank fontSize={21}/>
                ) : (
                  <MdOutlineIndeterminateCheckBox fontSize={21}/>
                )
              }
              loading={loading}
              onClick={onToggleCheck}
            />
          </Tooltip>
        )}

        <StyledSpace size={4}>
          <Button
            type={'text'}
            shape="circle"
            size="small"
            icon={
              <Badge
                count={
                  cleanObject(filters)
                    ? Object.keys(cleanObject(filters))?.length
                    : 0
                }
                size="small"
              >
                <MdOutlineFilterList fontSize={21}/>
              </Badge>
            }
            onClick={() => setOpenFilter(!openFilter)}
          />
        </StyledSpace>

        {!(activeTab === 'call' || allowSelection) && (
          <DropdownAny
            menu={{
              items: getMenuItems(currentSpace, filters, formatMessage),
              onClick: onMenuClick,
            }}
            trigger={['click']}
            onClick={(e: any) => e.stopPropagation()}
          >
            <Button
              type="text"
              shape="circle"
              size="small"
              icon={<MdOutlineMoreVert fontSize={21}/>}
            />
          </DropdownAny>
        )}
      </StyledRoot>

      {/*<Tooltip title="Filter Count" placement="left">*/}
      {/*  <StyledFilterBar>*/}
      {/*    <Text>Filter Count</Text>*/}
      {/*    <Badge*/}
      {/*      count={connectorData?.count || 0}*/}
      {/*      shape="square"*/}
      {/*      color="#796CFF"*/}
      {/*    ></Badge>*/}
      {/*  </StyledFilterBar>*/}
      {/*</Tooltip>*/}

      <StyledFilterContent
        className={clsx({
          active: openFilter,
        })}
      >
        <FilterForm
          tags={tags}
          filters={filters}
          clearFilter={() => setSearch('')}
          onApplyFilters={onApplyFilters}
        />
      </StyledFilterContent>

      <AppDrawer
        title={formatMessage({id: 'addContactDocLabels.title'})}
        open={open}
        onClose={() => setOpen(false)}
        width={720}
        showLoader
      >
        <ManageLabels
          labels={apiData}
          currentSpace={currentSpace ?? {}}
          reCallAPI={reCallAPI}
        />
      </AppDrawer>

      <AppSpaceCallModal
        idKey="document_id"
        filters={filters || {fetch_all: '1'}}
        onFinishSchedule={() => setOpenCallScheduler(false)}
        open={openCallScheduler}
        setOpen={setOpenCallScheduler}
      />
    </Fragment>
  );
};

export default SubHeader;
