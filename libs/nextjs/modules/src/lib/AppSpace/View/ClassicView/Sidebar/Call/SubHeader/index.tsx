import { useState } from 'react';
import type { MenuProps } from 'antd';
import { Badge, Button, Dropdown, Tooltip } from 'antd';
import {
  MdAdd,
  MdOutlineCheckBox,
  MdOutlineCheckBoxOutlineBlank,
  MdOutlineFilterList,
  MdOutlineIndeterminateCheckBox,
  MdOutlineMoreVert,
  MdRefresh,
} from 'react-icons/md';
import type { Spaces } from '@unpod/constants/types';
import {
  useAppSpaceActionsContext,
  useAppSpaceContext,
} from '@unpod/providers';
import SearchBox from './SearchBox';
import {
  StyledContent,
  StyledFilterContent,
  StyledRoot,
  StyledSpace,
} from './index.styled';
import { clsx } from 'clsx';
import FilterForm from './FilterForm';
import { cleanObject } from '@unpod/helpers/GlobalHelper';
import { useIntl } from 'react-intl';

const getMenuItems = (formatMessage: (msg: { id: string }) => string) => {
  return [
    {
      key: 'refresh',
      label: formatMessage({ id: 'common.refresh' }),
      icon: (
        <span className="ant-icon edit-icon">
          <MdRefresh fontSize={18} />
        </span>
      ),
    },
    {
      key: 'add-call',
      label: formatMessage({ id: 'sidebarMenu.addCall' }),
      icon: (
        <span className="ant-icon edit-icon">
          <MdAdd fontSize={18} />
        </span>
      ),
    },
  ];
};

type SubHeaderProps = {
  isDocsLoading?: boolean;
  onToggleCheck?: () => void;
  checkedType?: string;
  search: string;
  setSearch: (value: string) => void;
  filters: Record<string, unknown>;
  setFilters: (value: Record<string, unknown>) => void;
};

const SubHeader = ({
  isDocsLoading,
  onToggleCheck,
  checkedType = 'none',
  search,
  setSearch,
  filters,
  setFilters,
}: SubHeaderProps) => {
  const { callsActions } = useAppSpaceActionsContext();
  const { activeTab, currentSpace } = useAppSpaceContext();
  const { formatMessage } = useIntl();

  const [openFilter, setOpenFilter] = useState(false);
  const [searchCount] = useState(0);
  const allowSelection = activeTab === 'logs';

  const onApplyFilters = (appliedFilters: Record<string, unknown> | null) => {
    setFilters(appliedFilters ?? {});
    setOpenFilter(false);
  };

  const onMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'refresh') {
      (
        callsActions as {
          setQueryParams: (params: Record<string, unknown>) => void;
        }
      ).setQueryParams({ page: 1, page_size: 50 });
    } else if (key === 'add-call') {
      // Handle add call logic
      console.log('Add call clicked');
    }
  };

  return (
    <>
      <StyledRoot>
        <StyledContent>
          <SearchBox
            search={search}
            setSearch={setSearch}
            currentSpace={currentSpace as Spaces | null}
            searchCount={searchCount}
          />
        </StyledContent>

        {allowSelection && (
          <Tooltip title="Select All">
            <Button
              type="text"
              shape="circle"
              size="small"
              icon={
                checkedType === 'all' ? (
                  <MdOutlineCheckBox fontSize={21} />
                ) : checkedType === 'none' ? (
                  <MdOutlineCheckBoxOutlineBlank fontSize={21} />
                ) : (
                  <MdOutlineIndeterminateCheckBox fontSize={21} />
                )
              }
              loading={isDocsLoading}
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
                <MdOutlineFilterList fontSize={21} />
              </Badge>
            }
            onClick={() => setOpenFilter(!openFilter)}
          />
        </StyledSpace>

        {!allowSelection && (
          <Dropdown
            menu={{
              items: getMenuItems(formatMessage),
              onClick: onMenuClick,
            }}
            trigger={['click']}
          >
            <Button
              type="text"
              shape="circle"
              size="small"
              icon={<MdOutlineMoreVert fontSize={21} />}
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>
        )}
      </StyledRoot>

      <StyledFilterContent
        className={clsx({
          active: openFilter,
        })}
      >
        <FilterForm
          filters={filters}
          clearFilter={() => setSearch('')}
          onApplyFilters={onApplyFilters}
        />
      </StyledFilterContent>
    </>
  );
};

export default SubHeader;
