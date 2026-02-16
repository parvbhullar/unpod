import { useDrag, useDrop } from 'react-dnd';
import { type RenderHeaderCellProps } from '../models/data-grid';
import renderHeaderCell from '../renderHeaderCell';

type DraggableHeaderRendererProps<R> = RenderHeaderCellProps<R> & {
  onColumnsReorder: (sourceKey: string, targetKey: string) => void;};

export function DraggableHeaderRenderer<R>({
  onColumnsReorder,
  column,
  ...props
}: DraggableHeaderRendererProps<R>) {
  const [{ isDragging }, drag] = useDrag({
    type: 'COLUMN_DRAG',
    item: { key: column.key },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [{ isOver }, drop] = useDrop({
    accept: 'COLUMN_DRAG',
    drop({ key }: { key: string }) {
      onColumnsReorder(key, column.dataIndex);
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  });

  return (
    <div
      ref={(ref) => {
        drag(ref);
        drop(ref);
      }}
      style={{
        opacity: isDragging ? 0.5 : 1,
        backgroundColor: isOver ? '#ececec' : undefined,
        cursor: 'move',
      }}
    >
      {renderHeaderCell({ column, ...props })}
    </div>
  );
}
