import React, {useEffect, useMemo, useRef, useState} from 'react';
import type {InputRef} from 'antd';
import {Button, Divider, Tooltip} from 'antd';
import {MdClose, MdKeyboardArrowDown, MdKeyboardArrowUp, MdOutlineMoreVert,} from 'react-icons/md';
import clsx from 'clsx';
import {CalculatedColumn} from '../../models/data-grid';
import {EditCellState, SelectCellState} from '../../DataGrid';
import {PartialPosition} from '../../ScrollToCell';
import {StyledActions, StyledContainer, StyledInput} from './index.styled';
import {useDataGridConfiguration} from '../../DataGridContext';

type Props<R> = {
  isOpen?: boolean;
  rows: readonly R[];
  columns: readonly CalculatedColumn<R, any>[];
  setFindString: React.Dispatch<React.SetStateAction<string>>;
  setSelectedPosition: React.Dispatch<
    React.SetStateAction<SelectCellState | EditCellState<R>>
  >;
  setScrollToPosition: React.Dispatch<
    React.SetStateAction<PartialPosition | null>
  >;
  onMoreOptionsClick?: () => void;
  onClose: () => void;
  rowKeyId: string;
};

type FoundRecords = {
  idx: number;
  rowIdx: number;
  columnKey: string;
  value: string;
}[];

function FindRecord<R>({
                         isOpen,
                         rows,
                         columns,
                         setFindString,
                         setSelectedPosition,
                         setScrollToPosition,
                         onMoreOptionsClick,
                         onClose,
                         rowKeyId,
                       }: Props<R>) {
  const {allowFindReplace} = useDataGridConfiguration();

  const [totalMatches, setTotalMatches] = useState(0);
  const [findStr, setFindStr] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const foundRecordsRef = useRef<FoundRecords>([]);
  const [activeDirection, setActiveDirection] = useState<'up' | 'down'>('down');
  const inputRef = useRef<InputRef>(null);

  useEffect(() => {
    if (!isOpen) {
      setFindStr('');
      clearMatches();
      setTotalMatches(0);
    } else {
      inputRef.current!.focus({
        cursor: 'start',
      });
    }
  }, [isOpen]);

  const columnKeys = useMemo(
    () => columns.map((column) => column.dataIndex),
    [columns],
  );

  const clearMatches = () => {
    foundRecordsRef.current = [];
    setSelectedIdx(0);
  };

  const getSearchedRecords = (searchStr: string): FoundRecords => {
    const records: FoundRecords = [];

    for (let rowIdx = 0; rowIdx < rows.length; rowIdx++) {
      const row = rows[rowIdx];

      for (const columnKey in row) {
        if (
          columnKeys.includes(columnKey) &&
          String(row[columnKey]).toLowerCase().includes(searchStr.toLowerCase())
        ) {
          const foundcolumn = columns.find(
            (item) => item.dataIndex === columnKey,
          );
          if (foundcolumn)
            records.push({
              rowIdx: rowIdx,
              idx: foundcolumn.idx,
              columnKey: columnKey,
              value: String(row[columnKey]),
            });
        }
      }
    }

    return records;
  };

  const onSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setFindStr(value);
    setFindString(value);
    clearMatches();

    if (value) {
      setTotalMatches(getSearchedRecords(value).length);
    } else {
      setTotalMatches(0);
    }

    inputRef.current!.focus();
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

  const onFindUp = () => {
    setActiveDirection('up');
    if (foundRecordsRef.current.length === 0) {
      const searchedRecords = getSearchedRecords(findStr);

      if (searchedRecords.length > 0) {
        foundRecordsRef.current = searchedRecords;
        const lastIdx = searchedRecords.length - 1;
        goToCell(searchedRecords[lastIdx].idx, searchedRecords[lastIdx].rowIdx);

        setSelectedIdx(lastIdx);
      }
    } else {
      const nextIdx =
        selectedIdx > 0 ? selectedIdx - 1 : foundRecordsRef.current.length - 1;

      goToCell(
        foundRecordsRef.current[nextIdx].idx,
        foundRecordsRef.current[nextIdx].rowIdx,
      );

      setSelectedIdx(nextIdx);
    }
  };

  const onFindDown = () => {
    setActiveDirection('down');
    if (foundRecordsRef.current.length === 0) {
      const searchedRecords = getSearchedRecords(findStr);

      if (searchedRecords.length > 0) {
        foundRecordsRef.current = searchedRecords;
        const firstIdx = 0;

        goToCell(
          searchedRecords[firstIdx].idx,
          searchedRecords[firstIdx].rowIdx,
        );

        setSelectedIdx(firstIdx);
      }
    } else {
      const nextIdx =
        foundRecordsRef.current.length - 1 > selectedIdx ? selectedIdx + 1 : 0;

      goToCell(
        foundRecordsRef.current[nextIdx].idx,
        foundRecordsRef.current[nextIdx].rowIdx,
      );

      setSelectedIdx(nextIdx);
    }
  };

  return (
    <StyledContainer className={clsx({open: isOpen})}>
      <StyledInput
        ref={inputRef}
        placeholder="Find in data"
        value={findStr}
        onChange={onSearchChange}
        onPressEnter={activeDirection === 'down' ? onFindDown : onFindUp}
        suffix={
          <span>
            {findStr && (
              <span>
                {foundRecordsRef.current.length > 0
                  ? selectedIdx + 1
                  : totalMatches}
                {' of '}
                {totalMatches}
              </span>
            )}
          </span>
        }
      />

      <StyledActions>
        <Button
          type="text"
          icon={<MdKeyboardArrowUp fontSize={16}/>}
          disabled={findStr.length === 0}
          onClick={onFindUp}
        />
        <Button
          type="text"
          icon={<MdKeyboardArrowDown fontSize={16}/>}
          disabled={findStr.length === 0}
          onClick={onFindDown}
        />

        <Divider type="vertical" style={{borderColor: 'rgba(0,0,0,0.88)'}}/>

        {allowFindReplace && (
          <Tooltip title="More options">
            <Button
              type="text"
              onClick={onMoreOptionsClick}
              icon={<MdOutlineMoreVert fontSize={16}/>}
            />
          </Tooltip>
        )}

        <Button
          type="text"
          icon={<MdClose fontSize={16}/>}
          onClick={onClose}
        />
      </StyledActions>
    </StyledContainer>
  );
}

export default React.memo(FindRecord) as <R>(props: Props<R>) => JSX.Element;
