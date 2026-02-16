import { useDrag, useDrop } from 'react-dnd';
import clsx from 'clsx';
import { type RenderRowProps } from '../models/data-grid';
import { Row } from '..';

type DraggableRowRenderProps<R, SR> = RenderRowProps<R, SR> & {
  onRowReorder: (sourceIndex: number, targetIndex: number) => void;};

export function DraggableRowRenderer<R, SR>({
  rowIdx,
  isRowSelected,
  className,
  onRowReorder,
  ...props
}: DraggableRowRenderProps<R, SR>) {
  const [{ isDragging }, drag] = useDrag({
    type: 'ROW_DRAG',
    item: { index: rowIdx },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [{ isOver }, drop] = useDrop({
    accept: 'ROW_DRAG',
    drop({ index }: { index: number }) {
      onRowReorder(index, rowIdx);
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  className = clsx(className, {
    'row-dragging': isDragging,
    'row-over': isOver,
  });

  return (
    <Row
      ref={(ref) => {
        if (ref) {
          drag(ref.firstElementChild);
        }
        drop(ref);
      }}
      rowIdx={rowIdx}
      isRowSelected={isRowSelected}
      className={className}
      {...props}
    />
  );
}
