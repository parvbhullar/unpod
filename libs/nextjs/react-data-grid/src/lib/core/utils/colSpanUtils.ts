import type {CalculatedColumn, ColSpanArgs} from '../models/data-grid';

export function getColSpan<R, SR>(
  column: CalculatedColumn<R, SR>,
  lastLeftFixedColumnIndex: number,
  args: ColSpanArgs<R, SR>,
): number | undefined {
  const colSpan =
    typeof column.colSpan === 'function' ? column.colSpan(args) : 1;
  if (
    Number.isInteger(colSpan) &&
    colSpan! > 1 &&
    // ignore colSpan if it spans over both frozen and regular columns
    (!column.fixed || column.idx + colSpan! - 1 <= lastLeftFixedColumnIndex)
  ) {
    return colSpan!;
  }
  return undefined;
}
