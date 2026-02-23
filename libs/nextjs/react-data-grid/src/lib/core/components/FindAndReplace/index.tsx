import React, {useMemo, useRef, useState} from 'react';
import {Button, Checkbox, Typography} from 'antd';
import type {DraggableData, DraggableEvent} from 'react-draggable';
import Draggable from 'react-draggable';
import AppInput from '../AppInput';
import {EditCellState, SelectCellState} from '../../DataGrid';
import {CalculatedColumn, Maybe, RowsChangeData,} from '../../models/data-grid';
import ModalWindow from '../ModalWindow';
import {StyledActions, StyledContainer, StyledTitle} from './index.styled';
import {PartialPosition} from '../../ScrollToCell';

const {Group: CheckboxGroup} = Checkbox;
export type CheckboxValueType = string | number | boolean;

type Props<R> = {
  open: boolean;
  findString: string;
  rows: readonly R[];
  columns: readonly CalculatedColumn<R, any>[];
  onClose: () => void;
  setSelectedPosition: React.Dispatch<
    React.SetStateAction<SelectCellState | EditCellState<R>>
  >;
  setScrollToPosition: React.Dispatch<
    React.SetStateAction<PartialPosition | null>
  >;
  onRowsChange: Maybe<(rows: R[], data: RowsChangeData<R, any>) => void>;
  rowKeyId: string;
};

type FoundRecords = {
  idx: number;
  rowIdx: number;
  columnKey: string;
  value: string;
}[];

function FindAndReplace<R>({
                             open,
                             findString,
                             rows,
                             columns,
                             onClose,
                             setSelectedPosition,
                             setScrollToPosition,
                             onRowsChange,
                             rowKeyId,
                           }: Props<R>) {
  const [findStr, setFindStr] = useState(findString || '');
  const [replaceStr, setReplaceStr] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const foundRecordsRef = useRef<FoundRecords>([]);
  const [showLoopMsg, setShowLoopMsg] = useState(false);
  const [findReplaceMsg, setFindReplaceMsg] = useState('');
  const [searchConditions, setSearchConditions] = useState<CheckboxValueType[]>(
    [],
  );

  const [disabled, setDisabled] = useState(false);
  const [bounds, setBounds] = useState({
    left: 0,
    top: 20,
    bottom: 0,
    right: 0,
  });
  const draggleRef = useRef<HTMLDivElement>(null);

  const columnKeys = useMemo(
    () => columns.map((column) => column.dataIndex),
    [columns],
  );

  const clearMatches = () => {
    foundRecordsRef.current = [];
    setSelectedIdx(0);
  };

  const getSearchedRecords = (
    searchStr: string,
    conditions: CheckboxValueType[],
  ): FoundRecords => {
    const records: FoundRecords = [];

    for (let i = 0; i < rows.length; i++) {
      const obj = rows[i];
      for (const key in obj) {
        if (
          columnKeys.includes(key) &&
          String(obj[key]).toLowerCase().includes(searchStr.toLowerCase())
        ) {
          const foundcolumn = columns.find((item) => item.dataIndex === key);
          if (foundcolumn)
            records.push({
              rowIdx: i,
              idx: foundcolumn.idx,
              columnKey: key,
              value: String(obj[key]),
            });
        }
      }
    }

    if (conditions.includes('MC') && conditions.includes('MEC')) {
      return records.filter((item) => item.value == searchStr);
    } else if (conditions.includes('MC')) {
      return records.filter((item) => item.value.includes(searchStr));
    } else if (conditions.includes('MEC')) {
      return records.filter(
        (item) => item.value.toLowerCase() === searchStr.toLowerCase(),
      );
    } else {
      return records;
    }
  };

  const goToCell = (idx: number, rowIdx: number) => {
    setSelectedPosition({
      idx: idx,
      rowIdx,
      mode: 'SELECT',
      rowKey: rows[rowIdx]?.[rowKeyId as keyof R] as string | number,
      colKey: columns[idx].dataIndex,
    });
    setScrollToPosition({idx: idx, rowIdx});
  };

  const onFind = () => {
    setFindReplaceMsg('');
    if (foundRecordsRef.current.length === 0) {
      const searchedRecords = getSearchedRecords(findStr, searchConditions);

      if (searchedRecords.length > 0) {
        foundRecordsRef.current = searchedRecords;
        const firstIdx = 0;

        goToCell(
          searchedRecords[firstIdx].idx,
          searchedRecords[firstIdx].rowIdx,
        );

        setSelectedIdx(firstIdx);
      } else {
        setFindReplaceMsg(`There are no entries matching ${findStr}`);
      }
    } else {
      const nextIdx =
        foundRecordsRef.current.length - 1 > selectedIdx ? selectedIdx + 1 : 0;

      if (nextIdx === 0) {
        setShowLoopMsg(true);
      } else if (showLoopMsg) {
        setShowLoopMsg(false);
      }

      goToCell(
        foundRecordsRef.current[nextIdx].idx,
        foundRecordsRef.current[nextIdx].rowIdx,
      );

      setSelectedIdx(nextIdx);
    }
  };

  const replacedContent = (
    findStr: string,
    replaceStr: string,
    originalContent: string | number,
  ) => {
    // For string
    const regex = new RegExp(String(findStr), 'gi');
    if (isNaN(+originalContent)) {
      return (originalContent as string).replace(regex, replaceStr);
    }
    // For numbers
    else {
      return +String(originalContent).replace(regex, replaceStr);
    }
  };

  const findReplaceSearch = (
    foundData: { columnKey: string; rowIdx: number }[],
  ) => {
    const indexes: number[] = [];
    let columnKey = '';

    const updatedRows = rows.map((item: any, index) => {
      const searchedData = foundData.find((data) => data.rowIdx === index);
      if (searchedData) {
        indexes.push(index);
        columnKey = searchedData.columnKey;
        return {
          ...item,
          [searchedData.columnKey]: replacedContent(
            findStr,
            replaceStr,
            item?.[searchedData.columnKey],
          ),
        };
      }
      return item;
    });

    const column = columns.find((item) => item.dataIndex === columnKey);

    onRowsChange?.(updatedRows, {
      indexes: indexes,
      column: column!,
    });
  };

  const onReplace = () => {
    if (foundRecordsRef.current.length > 0) {
      const currentIdx =
        selectedIdx === 0
          ? foundRecordsRef.current.length - 1
          : selectedIdx - 1;

      findReplaceSearch([
        {
          columnKey: foundRecordsRef.current[currentIdx].columnKey,
          rowIdx: foundRecordsRef.current[currentIdx].rowIdx,
        },
      ]);

      setFindReplaceMsg(`Replaced ${findStr} with ${replaceStr}`);

      foundRecordsRef.current = foundRecordsRef.current.filter(
        (_, index) => index !== currentIdx,
      );

      if (foundRecordsRef.current?.[currentIdx]) {
        goToCell(
          foundRecordsRef.current[currentIdx].idx,
          foundRecordsRef.current[currentIdx].rowIdx,
        );
      } else if (foundRecordsRef.current?.[0]) {
        setSelectedIdx(1);
        goToCell(
          foundRecordsRef.current[0].idx,
          foundRecordsRef.current[0].rowIdx,
        );
      }
    }
  };
  const onReplaceAll = () => {
    if (foundRecordsRef.current) {
      const {current: records} = foundRecordsRef;
      const foundData = records.reduce(
        (acc: { columnKey: string; rowIdx: number }[], item) => {
          acc.push({columnKey: item.columnKey, rowIdx: item.rowIdx});
          return acc;
        },
        [],
      );

      findReplaceSearch(foundData);

      setFindReplaceMsg(
        `Replaced ${records.length} instances of ${findStr} with ${replaceStr}`,
      );

      clearMatches();
    }
  };

  const onCheckboxChange = (checkedValues: CheckboxValueType[]) => {
    setSearchConditions(checkedValues);
    clearMatches();
  };

  const onStart = (_event: DraggableEvent, uiData: DraggableData) => {
    const {clientWidth, clientHeight} = window.document.documentElement;
    const targetRect = draggleRef.current?.getBoundingClientRect();
    if (!targetRect) {
      return;
    }
    setBounds({
      left: -targetRect.left + uiData.x,
      right: clientWidth - (targetRect.right - uiData.x),
      top: -targetRect.top + uiData.y,
      bottom: clientHeight - (targetRect.bottom - uiData.y),
    });
  };

  return (
    <ModalWindow
      title={
        <StyledTitle
          onMouseOver={() => {
            if (disabled) {
              setDisabled(false);
            }
          }}
          onMouseOut={() => {
            setDisabled(true);
          }}
        >
          Find And Replace
        </StyledTitle>
      }
      style={{top: 20}}
      open={open}
      onCancel={onClose}
      mask={false}
      maskClosable={false}
      footer={null}
      width={430}
      destroyOnClose={false}
      modalRender={(modal) => (
        <Draggable
          disabled={disabled}
          bounds={bounds}
          nodeRef={draggleRef}
          onStart={(event, uiData) => onStart(event, uiData)}
        >
          <div ref={draggleRef}>{modal}</div>
        </Draggable>
      )}
    >
      <StyledContainer>
        <AppInput
          placeholder="Find"
          value={findStr}
          onChange={(event) => {
            setFindStr(event.target.value);
            clearMatches();
          }}
        />
        <AppInput
          placeholder="Replace With"
          value={replaceStr}
          onChange={(e) => setReplaceStr(e.target.value)}
        />

        <CheckboxGroup
          defaultValue={[]}
          onChange={onCheckboxChange}
          disabled={!findStr}
        >
          <Checkbox value="MC">Match Case</Checkbox>
          <Checkbox value="MEC">Match entire cell contents</Checkbox>
        </CheckboxGroup>

        {(showLoopMsg || findReplaceMsg) && (
          <Typography>
            {showLoopMsg && (
              <Typography.Paragraph style={{margin: 0}} strong>
                No more results found, looping around
              </Typography.Paragraph>
            )}

            {findReplaceMsg && (
              <Typography.Paragraph strong>
                {findReplaceMsg}
              </Typography.Paragraph>
            )}
          </Typography>
        )}

        <StyledActions>
          <Button
            type="primary"
            size="small"
            shape="round"
            disabled={findStr.length === 0}
            ghost
            onClick={onFind}
          >
            Find
          </Button>
          <Button
            type="primary"
            size="small"
            shape="round"
            ghost
            onClick={onReplace}
          >
            Replace
          </Button>
          <Button
            type="primary"
            size="small"
            shape="round"
            ghost
            onClick={onReplaceAll}
          >
            Replace All
          </Button>
          <Button type="primary" size="small" shape="round" onClick={onClose}>
            Done
          </Button>
        </StyledActions>
      </StyledContainer>
    </ModalWindow>
  );
}

export default FindAndReplace;
