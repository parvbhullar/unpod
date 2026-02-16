import { useEffect, useState } from 'react';
import { Button, Popover, Select } from 'antd';
import styled from 'styled-components';
// import './index.css';
import type { FilterDataType, RenderHeaderCellProps } from './models/data-grid';
import { FilterFilled, SearchOutlined } from '@ant-design/icons';
import { useDataGridConfiguration } from './DataGridContext';

const StyledHeaderRoot = styled.span`
  display: flex;
  justify-content: space-between;
  gap: 4px;
  width: 100%;
  height: 100%;
  cursor: pointer;
`;

const StyledFilterIcon = styled.span<{ fillColor: string }>`
  cursor: pointer;
  color: ${({ fillColor }: { fillColor: string }) =>
    fillColor !== ''
      ? fillColor
      : ({ theme }: { theme: any }) => theme.table.headerIconColor};
`;

const StyledHeaderName = styled.span`
  flex-grow: 1;
  overflow: hidden;
  overflow: clip;
  text-overflow: ellipsis;
`;

const StyledPopoverContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 180px;
`;

const StyledActionContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
`;

export default function renderHeaderCell<R, SR>({
  column,
  sortDirection,
  priority,
  onFilter,
  filterValue,
  headerColumnOptions,
  onSort,
  onClick,
}: RenderHeaderCellProps<R, SR>) {
  const gridConfig = useDataGridConfiguration();

  return (
    <StyledHeaderRoot>
      {/*{column.sorter ? (
        <SortableHeaderCell
          column={column}
          sortDirection={sortDirection}
          priority={priority}
          onSort={onSort}
          onClick={onClick}
        >
          {column.title}{' '}
          {gridConfig.allowGridActions &&
          gridConfig.allowFormula &&
          column.alphaIdx
            ? `(${column.alphaIdx})`
            : ''}
        </SortableHeaderCell>
      ) : (
        <StyledHeaderName
          style={{ textAlign: column.align ?? 'left' }}
          className='rdg-header-name'
          onClick={onClick}
        >
          {column.title}{' '}
          {gridConfig.allowGridActions &&
          gridConfig.allowFormula &&
          column.alphaIdx
            ? `(${column.alphaIdx})`
            : ''}
        </StyledHeaderName>
      )}*/}

      <StyledHeaderName
        style={{ textAlign: column.align ?? 'left' }}
        className="rdg-header-name"
        onClick={onClick}
      >
        {column.title}{' '}
        {gridConfig.allowGridActions &&
        gridConfig.allowFormula &&
        column.alphaIdx
          ? `(${column.alphaIdx})`
          : ''}
      </StyledHeaderName>

      <FilterHeaderCell
        filterValue={filterValue}
        column={column}
        onFilter={onFilter}
      />

      {headerColumnOptions}
    </StyledHeaderRoot>
  );
}

type SharedFilterHeaderCellProps<R, SR> = Pick<
  RenderHeaderCellProps<R, SR>,
  'filterValue' | 'column' | 'onFilter'
>;

function FilterHeaderCell<R, SR>({
  filterValue,
  column,
  onFilter,
}: SharedFilterHeaderCellProps<R, SR>) {
  const [open, onOpen] = useState(false);
  const [hasFilter, onSetFilter] = useState(false);
  const [selectedKeys, setSelectedKeys] = useState<FilterDataType>([]);

  useEffect(() => {
    if (filterValue) {
      setSelectedKeys(filterValue);
      onSetFilter(filterValue?.length > 0);
    }
  }, [filterValue]);

  const onSelectChange = (newValue: string) => {
    setSelectedKeys([newValue]);
  };

  const onConfirm = () => {
    onFilter(column.dataIndex, selectedKeys);
    onOpen(false);
  };

  const onClear = () => {
    setSelectedKeys([]);
    onFilter(column.dataIndex, null);
    onSetFilter(false);
    onOpen(false);
  };

  const onInputChange = (keys: FilterDataType) => {
    setSelectedKeys(keys);
  };

  const onOpenChange = (visible: boolean) => {
    onOpen(visible);
  };

  return (column.filterDropdown ?? column.filters) ? (
    <Popover
      placement="bottom"
      trigger="click"
      open={open}
      rootClassName="table-filter"
      content={
        column.filters ? (
          <StyledPopoverContainer>
            <StyledActionContainer>
              <Select
                value={selectedKeys?.[0] as any}
                style={{
                  width: '100%',
                }}
                onChange={onSelectChange}
              >
                {column.filters.map((filter, index) => (
                  <Select.Option key={index} value={filter.value as string}>
                    {filter.text}
                  </Select.Option>
                ))}
              </Select>
            </StyledActionContainer>

            <StyledActionContainer>
              <Button onClick={onClear} size="small">
                Reset
              </Button>
              <Button
                type="primary"
                onClick={onConfirm}
                icon={<SearchOutlined />}
                size="small"
              >
                Search
              </Button>
            </StyledActionContainer>
          </StyledPopoverContainer>
        ) : column.filterDropdown ? (
          column.filterDropdown({
            selectedKeys,
            setSelectedKeys: onInputChange,
            confirm: onConfirm,
            clearFilters: onClear,
            filters: column.filters,
            visible: hasFilter,
          })
        ) : null
      }
      onOpenChange={onOpenChange}
    >
      {column.filterIcon ? (
        column.filterIcon(hasFilter)
      ) : (
        <StyledFilterIcon fillColor={hasFilter ? '#1890ff' : ''}>
          <FilterFilled />
        </StyledFilterIcon>
      )}
    </Popover>
  ) : null;
}
