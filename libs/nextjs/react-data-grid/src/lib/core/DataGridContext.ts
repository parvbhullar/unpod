import { createContext, useContext } from 'react';
import type { GridConfiguration } from './models/data-grid';

export const defaultConfigurations: GridConfiguration = {
  allowGridActions: false,
  showSerialNoRow: true,
  allowRangeSelection: true,
  allowEditCell: true,
  allowUndoRedo: true,
  allowFormula: true,
  allowFindReplace: true,
  allowFindRecord: true,
  allowContextMenu: true,
  allowEditorToolbar: true,
  allowCountFooter: true,
  contextMenu: {
    allowCopy: true,
    allowCut: true,
    allowPaste: true,
    allowUndo: true,
    allowRedo: true,
    allowInsertRows: true,
    allowDeleteRows: true,
    allowAddColumns: true,
    allowDeleteColumns: true,
  },
  headerMenu: {
    allowSorting: true,
    allowAddColumn: true,
    allowRenameColumn: true,
    allowDeleteColumn: true,
    allowFilter: true,
  },
  editorToolbar: {
    allowUndo: true,
    allowRedo: true,
    allowBold: true,
    allowItalic: true,
    allowStrikeThrough: true,
    allowFillColor: true,
    allowTextColor: true,
    allowUnderline: true,
    allowFormula: true,
    allowFormulaInput: true,
  },
};

const DataGridContext = createContext<GridConfiguration>(defaultConfigurations);

export const DataGridProvider = DataGridContext.Provider;

export function useDataGridConfiguration(): GridConfiguration {
  return useContext(DataGridContext);
}
