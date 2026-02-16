import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';

import { useLatestFunc } from './hooks';
import {
  createCellEvent,
  getCellClassname,
  getCellStyle,
  onEditorNavigation,
} from './utils';
import type {
  CellKeyboardEvent,
  CellRendererProps,
  EditCellKeyDownArgs,
  Maybe,
  Omit,
  RenderEditCellProps,
} from './models/data-grid';
import { StyledCellWrapper } from './style/cell';

/*
 * To check for outside `mousedown` events, we listen to all `mousedown` events at their birth,
 * i.e. on the window during the capture phase, and at their death, i.e. on the window during the bubble phase.
 *
 * We schedule a check at the birth of the event, cancel the check when the event reaches the "inside" container,
 * and trigger the "outside" callback when the event bubbles back up to the window.
 *
 * The event can be `stopPropagation()`ed halfway through, so they may not always bubble back up to the window,
 * so an alternative check must be used. The check must happen after the event can reach the "inside" container,
 * and not before it run to completion. `requestAnimationFrame` is the best way we know how to achieve this.
 * Usually we want click event handlers from parent components to access the latest commited values,
 * so `mousedown` is used instead of `click`.
 *
 * We must also rely on React's event capturing/bubbling to handle elements rendered in a portal.
 */

const CellEditing = styled(StyledCellWrapper)`
  &.cell-editing {
    padding: 0;
  }
`;

type SharedCellRendererProps<R, SR> = Pick<CellRendererProps<R, SR>, 'colSpan'>;

type EditCellProps<R, SR> = Omit<RenderEditCellProps<R, SR>, 'onRowChange' | 'onClose'> & SharedCellRendererProps<R, SR> & {
  rowIdx: number;
  onRowChange: (
    row: R,
    commitChanges: boolean,
    shouldFocusCell: boolean,
  ) => void;
  closeEditor: (shouldFocusCell: boolean) => void;
  navigate: (event: React.KeyboardEvent<HTMLDivElement>) => void;
  onKeyDown: Maybe<
    (args: EditCellKeyDownArgs<R, SR>, event: CellKeyboardEvent) => void
  >;
  dataKey: keyof R;
  showBorder: boolean;
  rowSelectionType: 'radio' | 'checkbox';
  autoRowHeight: boolean;
  onCellEditFinish: (row: R, rowIdx: number) => void;};

export default function EditCell<R, SR>({
  column,
  colSpan,
  row,
  rowIdx,
  onRowChange,
  closeEditor,
  onKeyDown,
  navigate,
  dataKey,
  showBorder,
  rowSelectionType,
  autoRowHeight,
  onCellEditFinish,
}: EditCellProps<R, SR>) {
  const frameRequestRef = useRef<number | undefined>(undefined);
  const currentEditedRef = useRef<R | undefined>(undefined);
  const commitOnOutsideClick =
    column.editorOptions?.commitOnOutsideClick !== false;

  // We need to prevent the `useEffect` from cleaning up between re-renders,
  // as `onWindowCaptureMouseDown` might otherwise miss valid mousedown events.
  // To that end we instead access the latest props via useLatestFunc.
  const commitOnOutsideMouseDown = useLatestFunc(() => {
    onClose(true, false);
  });

  function onChangeFinish() {
    if (currentEditedRef.current) {
      onCellEditFinish(currentEditedRef.current, rowIdx);
      currentEditedRef.current = undefined;
    }
  }

  useEffect(() => {
    if (!commitOnOutsideClick) return;

    function onWindowCaptureMouseDown() {
      onChangeFinish();
      frameRequestRef.current = requestAnimationFrame(commitOnOutsideMouseDown);
    }

    addEventListener('mousedown', onWindowCaptureMouseDown, { capture: true });

    return () => {
      removeEventListener('mousedown', onWindowCaptureMouseDown, {
        capture: true,
      });
      cancelFrameRequest();
    };
  }, [commitOnOutsideClick, commitOnOutsideMouseDown]);

  function cancelFrameRequest() {
    cancelAnimationFrame(frameRequestRef.current!);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (onKeyDown) {
      const cellEvent = createCellEvent(event);
      onKeyDown(
        {
          mode: 'EDIT',
          row,
          column,
          rowIdx,
          navigate() {
            navigate(event);
          },
          onClose,
        },
        cellEvent,
      );
      if (cellEvent.isGridDefaultPrevented()) return;
    }

    if (event.key === 'Escape') {
      // Discard changes
      onClose();
    } else if (event.key === 'Enter') {
      onChangeFinish();
      onClose(true);
    } else if (onEditorNavigation(event)) {
      navigate(event);
    }
  }

  function onClose(commitChanges = false, shouldFocusCell = true) {
    if (commitChanges) {
      onRowChange(row, true, shouldFocusCell);
    } else {
      closeEditor(shouldFocusCell);
    }
  }

  function onEditorRowChange(row: R, commitChangesAndFocus = false) {
    currentEditedRef.current = row;
    if (commitChangesAndFocus) {
      onChangeFinish();
    }
    onRowChange(row, commitChangesAndFocus, commitChangesAndFocus);
  }

  const { cellClass } = column;
  const className = getCellClassname(
    column,
    'rdg-editor-container',
    !column.editorOptions?.displayCellContent && 'cell-editing',
    typeof cellClass === 'function' ? cellClass(row) : cellClass,
    showBorder && 'show-border',
  );

  return (
    <CellEditing
      role="gridcell"
      aria-colindex={column.idx + 1} // aria-colindex is 1-based
      aria-colspan={colSpan}
      aria-selected
      className={className}
      style={getCellStyle(column, colSpan)}
      onKeyDown={handleKeyDown}
      onMouseDownCapture={cancelFrameRequest}
      $autoRowHeight={autoRowHeight}
    >
      {column.renderEditCell != null && (
        <>
          {column.renderEditCell({
            column,
            row,
            onRowChange: onEditorRowChange,
            onClose,
          })}
          {column.editorOptions?.displayCellContent &&
            (column.render
              ? column.render(row[dataKey], row, rowIdx)
              : column.renderCell({
                  column,
                  row,
                  isCellEditable: true,
                  tabIndex: -1,
                  onRowChange: onEditorRowChange,
                  rowSelectionType,
                }))}
        </>
      )}
    </CellEditing>
  );
}
