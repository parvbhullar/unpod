import React, {Fragment, useEffect, useMemo, useState} from 'react';
import {Button, Select, Space, Typography} from 'antd';
import {MdAdd, MdCheck, MdClose, MdDeleteOutline, MdEdit, MdFilterAlt, MdSettings,} from 'react-icons/md';
import clsx from 'clsx';
import type {
  CalculatedColumn,
  LocalFilter,
  Maybe,
  MenuItemProps,
  SortDirection,
  TableCellItemProps,
  UndoRedoProcessProps,
} from '../../models/data-grid';

import {
  StyledActions,
  StyledDatePicker,
  StyledFilterContainer,
  StyledFlexRow,
  StyledInput,
  StyledInputNumber,
  StyledMoreHandle,
  StyledPopover,
  StyledRangePicker,
  StyledRoot,
  StyledSelect,
  StyledTitleContainer,
} from './index.styled';
import NewColumnWindow from '../NewColumnWindow';
import Menus from '../Menus';
import {BsSortAlphaDown, BsSortAlphaDownAlt} from 'react-icons/bs';
import {useDataGridConfiguration} from '../../DataGridContext';

const {Paragraph, Text} = Typography;

type OperatorOption = {
  label: string;
  value: string;
};

type Props<TRow, TSummaryRow = unknown> = {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  column: CalculatedColumn<TRow, TSummaryRow>;
  columns: readonly any[];
  onInsertCell?: (
    data: TableCellItemProps,
    callback?: (data: any) => void,
  ) => void;
  onDeleteCells?: (
    startIdx: number,
    count: number,
    callback?: (data: any) => void,
  ) => void;
  onRenameColumn?: (
    columnKey: string,
    newTitle: string,
    callback?: (data: any) => void,
  ) => void;
  onSort?: (ctrlClick: boolean, customDir?: SortDirection) => void;
  onLocalFiltersChange?: Maybe<
    Maybe<React.Dispatch<React.SetStateAction<LocalFilter[]>>>
  >;
  saveVersionHistory(data: UndoRedoProcessProps): void;
  [key: string]: any;
};

type InputType = string | number;
type ObjectInputType = { start: InputType; end: InputType };

const HeaderColumnOptions = <R, SR>({
                                      open,
                                      setOpen,
                                      column,
                                      columns,
                                      onInsertCell,
                                      onDeleteCells,
                                      onSort,
                                      onRenameColumn,
                                      onLocalFiltersChange,
                                      saveVersionHistory,
                                      ...restProps
                                    }: Props<R, SR>) => {
  const {headerMenu} = useDataGridConfiguration();
  const [allowRename, setAllowRename] = useState(false);
  const [filterApplied, setFilterApplied] = useState(false);
  const [openModal, setOpenModal] = useState(false);
  const [condition, setCondition] = useState<any>(null);
  const [inputVal, setInputVal] = useState<
    InputType | ObjectInputType | null
  >();
  const [columnName, setColumnName] = useState<string | null>(null);

  const isAllowed = useMemo(() => {
    return (
      headerMenu.allowSorting ||
      headerMenu.allowFilter ||
      headerMenu.allowAddColumn ||
      headerMenu.allowDeleteColumn ||
      headerMenu.allowRenameColumn
    );
  }, [headerMenu]);

  useEffect(() => {
    if (column.title && typeof column.title === 'string') {
      setColumnName(column.title);
    }
  }, [column.title]);

  const onClickAddColumn = () => {
    setOpenModal(true);
  };

  const handleInsertColumn = (data: any) => {
    onInsertCell?.(data, saveVersionHistory);
    setOpenModal(false);
  };

  /**
   * Handle delete cell(s)
   */
  const handleDeleteCells = () => {
    onDeleteCells?.(column.idx - 1, 1, saveVersionHistory);
  };

  /**
   * Handle rename column
   */
  const handleRenameColumn = () => {
    setAllowRename(true);
  };

  const handleRenameClick = () => {
    if (columnName) {
      onRenameColumn?.(column.dataIndex, columnName, (data) => {
        saveVersionHistory(data);
        setOpen(false);
      });
    }
  };

  const {items, operators} = useMemo((): {
    items: MenuItemProps[];
    operators: OperatorOption[];
  } => {
    const menuItems: MenuItemProps[] = [];

    if (headerMenu.allowSorting && onSort) {
      menuItems.push({
        icon: <BsSortAlphaDown fontSize={18}/>,
        label: `Sort column A to Z`,
        onClick: (event) => {
          onSort(event.ctrlKey || event.metaKey, 'ASC');
        },
      });
      menuItems.push({
        icon: <BsSortAlphaDownAlt fontSize={18}/>,
        label: `Sort column Z to A`,
        onClick: (event) => {
          onSort(event.ctrlKey || event.metaKey, 'DESC');
        },
      });
    }

    if (headerMenu.allowAddColumn && onInsertCell) {
      menuItems.push({
        icon: <MdAdd fontSize={18}/>,
        label: `Add column`,
        onClick: onClickAddColumn,
      });
    }

    if (headerMenu.allowDeleteColumn && onDeleteCells) {
      menuItems.push({
        icon: <MdDeleteOutline fontSize={20}/>,
        label: 'Delete column',
        confirmWindowProps: {
          onConfirm: handleDeleteCells,
          title: 'Delete Column',
          content: 'Are you sure to delete this column?',
        },
      });
    }

    if (headerMenu.allowRenameColumn && onRenameColumn) {
      menuItems.push({
        icon: <MdEdit fontSize={16}/>,
        label: `Rename column`,
        onClick: handleRenameColumn,
      });
    }

    const operatorOptions: OperatorOption[] = [
      {
        label: 'Equal',
        value: 'eq',
      },
      {
        label: 'Not equal',
        value: 'neq',
      },
    ];

    if (column.dataType === 'number' || column.dataType === 'integer') {
      operatorOptions.push(
        {
          label: 'Greater than',
          value: 'gt',
        },
        {
          label: 'Greater than or equal',
          value: 'gte',
        },
        {
          label: 'Less than',
          value: 'lt',
        },
        {
          label: 'Less than or equal',
          value: 'lte',
        },
        {
          label: 'Is Between',
          value: 'ibt',
        },
        {
          label: 'Is Not Between',
          value: 'nibt',
        },
      );
    } else if (column.dataType === 'date') {
      operatorOptions.push(
        {
          label: 'Is Between',
          value: 'ibt',
        },
        {
          label: 'Is Not Between',
          value: 'nibt',
        },
      );
    } else {
      operatorOptions.push(
        {
          label: 'Contains',
          value: 'contains',
        },
        {
          label: 'Does not contain',
          value: 'notContains',
        },
        {
          label: 'Starts with',
          value: 'startsWith',
        },
        {
          label: 'Ends with',
          value: 'endsWith',
        },
      );
    }

    return {items: menuItems, operators: operatorOptions};
  }, [onInsertCell, onDeleteCells, onRenameColumn, headerMenu]);

  const handleApplyClick = () => {
    if (condition && inputVal) {
      onLocalFiltersChange?.((prev) => {
        const isExist = prev?.find((f) => f.columnKey === column.dataIndex);
        if (isExist) {
          return (prev || []).map((f) =>
            f.columnKey === column.dataIndex
              ? {...f, operator: condition, inputVal: inputVal}
              : f,
          );
        }

        const newFilter: LocalFilter = {
          columnKey: column.dataIndex,
          operator: condition,
          inputVal: inputVal,
          dataType: column.dataType,
        };

        return [...(prev || []), newFilter];
      });

      setFilterApplied(true);
      setOpen(false);
    }
  };

  const handleClearClick = () => {
    // setCondition(null);
    setInputVal('');
    onLocalFiltersChange?.((prev) => {
      return (prev || []).filter((f) => f.columnKey !== column.dataIndex);
    });
    // onFilter(column.dataIndex, null);
    // setOpen(false);
    setFilterApplied(false);
  };

  const content = (
    <StyledRoot>
      <StyledTitleContainer>
        <div className="ant-popover-title">
          <MdSettings fontSize={16}/>
          <Text>Column: {column.title}</Text>
        </div>
      </StyledTitleContainer>

      <Menus items={items}/>

      {headerMenu.allowRenameColumn && allowRename && (
        <StyledFlexRow>
          <StyledInput
            placeholder="Column Name"
            value={columnName as string}
            onChange={(event) => setColumnName(event.target.value)}
          />

          <Space size="small">
            <Button
              type="primary"
              size="small"
              shape="circle"
              onClick={handleRenameClick}
              icon={<MdCheck fontSize={18}/>}
              disabled={!columnName}
            />

            <Button
              type="primary"
              size="small"
              shape="circle"
              onClick={() => setAllowRename(false)}
              icon={<MdClose fontSize={18}/>}
              ghost
            />
          </Space>
        </StyledFlexRow>
      )}

      {headerMenu.allowFilter && (
        <Fragment>
          <StyledFilterContainer>
            <Paragraph style={{marginBottom: 0}} strong>
              Filter
            </Paragraph>
            <StyledSelect
              placeholder="None"
              value={condition}
              onChange={setCondition}
            >
              {operators.map((operator) => (
                <Select.Option key={operator.value} value={operator.value}>
                  {operator.label}
                </Select.Option>
              ))}
            </StyledSelect>

            {column.dataType === 'number' || column.dataType === 'integer' ? (
              condition === 'ibt' || condition === 'nibt' ? (
                <Space>
                  <StyledInputNumber
                    placeholder="Start"
                    value={(inputVal as ObjectInputType)?.start as number}
                    onChange={(newValue) =>
                      setInputVal((prev) => ({
                        ...(prev as ObjectInputType),
                        start: newValue as number,
                      }))
                    }
                  />
                  <StyledInputNumber
                    placeholder="End"
                    value={(inputVal as ObjectInputType)?.end as number}
                    onChange={(newValue) =>
                      setInputVal((prev) => ({
                        ...(prev as ObjectInputType),
                        end: newValue as number,
                      }))
                    }
                  />
                </Space>
              ) : (
                <StyledInputNumber
                  placeholder="Number"
                  value={inputVal as number}
                  onChange={(newValue) => setInputVal(newValue)}
                />
              )
            ) : column.dataType === 'date' ? (
              condition === 'ibt' || condition === 'nibt' ? (
                <StyledRangePicker
                  onChange={(date) =>
                    setInputVal({
                      start: date?.[0]?.toISOString() as string,
                      end: date?.[1]?.toISOString() as string,
                    })
                  }
                />
              ) : (
                <StyledDatePicker
                  placeholder="Date"
                  onChange={(date) => setInputVal(date?.toString())}
                />
              )
            ) : (
              <StyledInput
                placeholder="Value"
                value={inputVal as string}
                onChange={(event) =>
                  setInputVal(event.target.value.toString().toLowerCase())
                }
                onPressEnter={handleApplyClick}
              />
            )}
          </StyledFilterContainer>

          <StyledActions>
            <Button
              type="primary"
              size="small"
              shape="round"
              onClick={handleClearClick}
              disabled={!condition || !inputVal}
              ghost
            >
              Clear
            </Button>

            <Button
              type="primary"
              size="small"
              shape="round"
              onClick={handleApplyClick}
              disabled={!condition || !inputVal}
            >
              Apply
            </Button>
          </StyledActions>
        </Fragment>
      )}
    </StyledRoot>
  );

  return (
    <React.Fragment>
      {isAllowed && (
        <StyledPopover
          content={content}
          trigger="click"
          overlayStyle={{zIndex: 1000}}
          overlayInnerStyle={{padding: 0, borderRadius: 12}}
          {...restProps}
          onOpenChange={(visible) => {
            setOpen(visible);
            setAllowRename(false);
          }}
          open={open}
        >
          <StyledMoreHandle className={clsx({active: open})}>
            {filterApplied && <MdFilterAlt fontSize={16}/>}
          </StyledMoreHandle>
        </StyledPopover>
      )}

      {column.idx >= 0 && openModal && (
        <NewColumnWindow
          open={openModal}
          onCancel={() => setOpenModal(false)}
          columns={columns}
          idx={column.idx}
          onAddColumn={handleInsertColumn}
        />
      )}
    </React.Fragment>
  );
};

export default HeaderColumnOptions;
