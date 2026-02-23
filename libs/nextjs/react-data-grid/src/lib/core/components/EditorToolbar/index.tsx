import type {CSSProperties} from 'react';
import {useMemo, useState} from 'react';
import {Popover, Tooltip} from 'antd';
import {BiSolidColorFill} from 'react-icons/bi';
import {TbMathFunction} from 'react-icons/tb';
import {ImTextColor} from 'react-icons/im';
import {
  MdOutlineFormatBold,
  MdOutlineFormatItalic,
  MdOutlineFormatStrikethrough,
  MdRedo,
  MdUndo,
} from 'react-icons/md';
import clsx from 'clsx';
import ColorPalette from './ColorPalette';
import {SelectCellState} from '../../DataGrid';
import {
  StyledButton,
  StyledColorButton,
  StyledFillColor,
  StyledInput,
  StyledRoot,
  StyledToolbarRoot,
} from './index.styled';
import {CalculatedColumn} from '../..';
import FormulaMenu from './FormulaMenu';
import type {GridCellStyleType, GridFormulaType,} from '../../models/data-grid';
import {useDataGridConfiguration} from '../../DataGridContext';

type Props<R> = {
  rows: readonly R[];
  columns: readonly CalculatedColumn<R, any>[];
  cellSavedStyles: GridCellStyleType[];
  rowKeyId: string;
  selectedPosition: SelectCellState;
  onStylePropsChange: (styleProps: CSSProperties) => void;
  canUndo: boolean;
  onUndo: () => void;
  canRedo: boolean;
  onRedo: () => void;
  draggedOverCellIdx?: number;
  draggedOverRowIdx?: number;
  formulas: GridFormulaType[];
  onUpdateFormula(position: SelectCellState, customValue?: string): void;
};

function EditorToolbar<R>({
                            rows,
                            columns,
                            cellSavedStyles,
                            rowKeyId,
                            selectedPosition,
                            onStylePropsChange,
                            canUndo,
                            onUndo,
                            canRedo,
                            onRedo,
                            draggedOverCellIdx,
                            draggedOverRowIdx,
                            formulas,
                            onUpdateFormula,
                          }: Props<R>) {
  const {editorToolbar} = useDataGridConfiguration();

  const [openTextColor, setOpenTextColor] = useState(false);
  const [openFillColor, setOpenFillColor] = useState(false);
  const [currFormula, setCurrFormula] = useState<string | undefined>(undefined);

  const isAllowed = useMemo(() => {
    return Object.values(editorToolbar).some((item) => item);
  }, [editorToolbar]);

  const isShowToolbar = useMemo(() => {
    const {allowFormulaInput, ...restProps} = editorToolbar;
    return Object.values(restProps).some((item) => item);
  }, [editorToolbar]);

  const activeStyle = useMemo((): CSSProperties => {
    if (selectedPosition.idx >= 0) {
      const row = rows[selectedPosition.rowIdx];
      if (row) {
        const rowUniqueId = row[rowKeyId as keyof R];
        const dataIndex = columns[selectedPosition.idx].dataIndex as keyof R;

        const cellSavedStyle = cellSavedStyles?.find(
          (item) => item.colKey === dataIndex && item.rowKey === rowUniqueId,
        );

        const cellFormula = formulas?.find(
          (item) => item.colKey === dataIndex && item.rowKey === rowUniqueId,
        );

        setCurrFormula(cellFormula?.formula || undefined);

        return cellSavedStyle?.style || {};
      }
    }

    return {} as CSSProperties;
  }, [rows, columns, selectedPosition, cellSavedStyles, formulas]);

  const onChangeFormula = (value: string) => {
    if (selectedPosition.idx >= 0) {
      setCurrFormula(value);
      onUpdateFormula(selectedPosition, value);
    }
  };

  const onColorSelect = (color: string, type: 'text' | 'fill') => {
    onStylePropsChange(
      type === 'text' ? {color} : {backgroundColor: color},
    );
  };

  return isAllowed ? (
    <StyledRoot>
      {editorToolbar.allowFormulaInput && (
        <StyledInput
          prefix={<TbMathFunction fontSize={18}/>}
          value={currFormula}
          onChange={(e) => onChangeFormula(e.target.value)}
        />
      )}

      {isShowToolbar && (
        <StyledToolbarRoot>
          {editorToolbar.allowUndo && (
            <Tooltip title="Undo (Ctrl+Z)">
              <StyledButton
                size="small"
                type="text"
                onClick={onUndo}
                disabled={!canUndo}
              >
                <MdUndo fontSize={18}/>
              </StyledButton>
            </Tooltip>
          )}

          {editorToolbar.allowRedo && (
            <Tooltip title="Redo (Ctrl+Alt+Z)">
              <StyledButton
                size="small"
                type="text"
                onClick={onRedo}
                disabled={!canRedo}
              >
                <MdRedo fontSize={18}/>
              </StyledButton>
            </Tooltip>
          )}

          {editorToolbar.allowBold && (
            <Tooltip title="Bold (Ctrl+B)">
              <StyledButton
                size="small"
                type="text"
                className={clsx({
                  selected: activeStyle.fontWeight === 'bold',
                })}
                onClick={() => onStylePropsChange({fontWeight: 'bold'})}
              >
                <MdOutlineFormatBold fontSize={18}/>
              </StyledButton>
            </Tooltip>
          )}

          {editorToolbar.allowItalic && (
            <Tooltip title="Italic (Ctrl+I)">
              <StyledButton
                size="small"
                type="text"
                className={clsx({
                  selected: activeStyle.fontStyle === 'italic',
                })}
                onClick={() => onStylePropsChange({fontStyle: 'italic'})}
              >
                <MdOutlineFormatItalic fontSize={18}/>
              </StyledButton>
            </Tooltip>
          )}

          {editorToolbar.allowStrikeThrough && (
            <Tooltip title="Strikethrough (Ctrl+Shift+5)">
              <StyledButton
                size="small"
                type="text"
                className={clsx({
                  selected: activeStyle.textDecoration === 'line-through',
                })}
                onClick={() =>
                  onStylePropsChange({textDecoration: 'line-through'})
                }
              >
                <MdOutlineFormatStrikethrough fontSize={18}/>
              </StyledButton>
            </Tooltip>
          )}

          {editorToolbar.allowTextColor && (
            <Popover
              placement="bottom"
              content={
                <ColorPalette
                  activeColor={activeStyle.color || '#1F1F1F'}
                  type="text"
                  onColorSelect={onColorSelect}
                />
              }
              trigger="click"
              onOpenChange={(open) => {
                if (open) setOpenTextColor(false);
              }}
              overlayInnerStyle={{padding: 0}}
            >
              <Tooltip
                title="Text Color"
                open={openTextColor}
                onOpenChange={setOpenTextColor}
              >
                <StyledColorButton size="small" type="text">
                  <ImTextColor/>
                  <StyledFillColor
                    style={{
                      backgroundColor: activeStyle.color || '#1F1F1F',
                    }}
                  />
                </StyledColorButton>
              </Tooltip>
            </Popover>
          )}

          {editorToolbar.allowFillColor && (
            <Popover
              placement="bottom"
              content={
                <ColorPalette
                  activeColor={activeStyle.backgroundColor || '#ffffff'}
                  type="fill"
                  onColorSelect={onColorSelect}
                />
              }
              trigger="click"
              onOpenChange={(open) => {
                if (open) setOpenFillColor(false);
              }}
              overlayInnerStyle={{padding: 0}}
            >
              <Tooltip
                title="Fill Color"
                open={openFillColor}
                onOpenChange={setOpenFillColor}
              >
                <StyledColorButton size="small" type="text">
                  <BiSolidColorFill/>
                  <StyledFillColor
                    style={{
                      backgroundColor: activeStyle.backgroundColor || '#fff',
                    }}
                  />
                </StyledColorButton>
              </Tooltip>
            </Popover>
          )}

          {editorToolbar.allowFormula && (
            <FormulaMenu
              columns={columns}
              draggedOverCellIdx={draggedOverCellIdx}
              draggedOverRowIdx={draggedOverRowIdx}
              selectedPosition={selectedPosition}
              onUpdateFormula={onUpdateFormula}
            />
          )}
        </StyledToolbarRoot>
      )}
    </StyledRoot>
  ) : null;
}

export default EditorToolbar;
