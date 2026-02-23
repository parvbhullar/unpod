import React, {useEffect, useState} from 'react';
import {FunctionOutlined} from '@ant-design/icons';
import {SelectCellState} from '../../DataGrid';
import {CalculatedColumn, GridFormulaType} from '../../models/data-grid';
import {StyledFormulaInput} from './index.styled';

type Props<R> = {
  rows: readonly R[];
  columns: readonly CalculatedColumn<R, any>[];
  formulas: GridFormulaType[];
  selectedPosition: SelectCellState;
  onUpdateFormula(position: SelectCellState, customValue?: string): void;
  rowKeyId: string;
};

function FormulaInput<R>({
                           rows,
                           columns,
                           formulas,
                           selectedPosition,
                           onUpdateFormula,
                           rowKeyId,
                         }: Props<R>) {
  const [currFormula, setCurrFormula] = useState<string | undefined>(undefined);

  const dataIndex =
    selectedPosition?.colKey && selectedPosition?.colKey !== ''
      ? selectedPosition?.colKey
      : (columns[selectedPosition.idx]?.dataIndex as keyof R);
  const rowId =
    selectedPosition?.rowKey && selectedPosition?.rowKey !== ''
      ? selectedPosition?.rowKey
      : rows?.[selectedPosition.rowIdx]?.[rowKeyId as keyof R];

  const cellFormula =
    formulas?.find((item) => item.colKey === dataIndex && item.rowKey === rowId)
      ?.formula || undefined;

  useEffect(() => {
    setCurrFormula(cellFormula);
  }, [cellFormula, selectedPosition.idx, selectedPosition.rowIdx]);

  const onChangeFormula = (value: string) => {
    setCurrFormula(value);
    onUpdateFormula(selectedPosition, value);
  };

  return (
    <StyledFormulaInput
      prefix={<FunctionOutlined/>}
      value={currFormula}
      disabled={selectedPosition.idx < 0}
      onChange={(e) => onChangeFormula(e.target.value)}
    />
  );
}

export default FormulaInput;
