import { Parser as FormulaParser } from 'hot-formula-parser';
import { CalculatedColumn } from '..';
import { getHeaderCellAlphaIdx, getHeaderCellNumIdx } from '.';

const parser = new FormulaParser();
const cellReferenceRegex = /([A-Z]+)([0-9]+)/g;

function replaceCharToData<R, SR>(
  rows: readonly R[],
  columns: readonly CalculatedColumn<R, SR>[],
  expression: string,
) {
  return expression.replace(cellReferenceRegex, (_, alphaIdx, rowIdx) => {
    const dataIndex = columns.find(
      (col) => col.alphaIdx === alphaIdx,
    )?.dataIndex;

    return dataIndex ? (rows as any)[rowIdx - 1][dataIndex] || 0 : 0;
  });
}

export function evaluateFormula<R, SR>(
  rows: readonly R[],
  columns: readonly CalculatedColumn<R, SR>[],
  formula: string,
) {
  try {
    const expression = formula.slice(1).toUpperCase();

    if (formula.includes(':')) {
      const rangeRegex = /([A-Z]+)(\d+):([A-Z]+)(\d+)/g;

      const replacedValues = expression.replace(
        rangeRegex,
        (match, col1, row1, col2, row2) => {
          const startRow = parseInt(row1);
          const endRow = parseInt(row2);
          const col = col1;

          const expandedRange = [];

          if (col1 === col2) {
            for (let i = startRow; i <= endRow; i++) {
              expandedRange.push(`${col}${i}`);
            }
          } else {
            const colIdx1 = getHeaderCellNumIdx(col1);
            const colIdx2 = getHeaderCellNumIdx(col2);

            const startIdx = Math.min(colIdx1, colIdx2);
            const endIdx = Math.max(colIdx1, colIdx2);

            for (let i = startIdx; i <= endIdx; i++) {
              const currCol = getHeaderCellAlphaIdx(i);
              for (let j = startRow; j <= endRow; j++) {
                expandedRange.push(`${currCol}${j}`);
              }
            }
          }

          return expandedRange.join(',');
        },
      );

      return (
        +Number(
          parser.parse(replaceCharToData(rows, columns, replacedValues)).result,
        ).toFixed(2) || 0
      );
    }

    return (
      +Number(
        parser.parse(replaceCharToData(rows, columns, expression)).result,
      ).toFixed(2) || 0
    );
  } catch (error) {
    return 0;
  }
}

export const isCorrectFormula = (formula: string) => {
  if (formula) {
    const { startBracCount, endBracCount } = formula.split('').reduce(
      (acc, val) => {
        if (val === '(') ++acc.startBracCount;
        else if (val === ')') ++acc.endBracCount;

        return acc;
      },
      { startBracCount: 0, endBracCount: 0 },
    );
    return endBracCount > 0 && startBracCount === endBracCount;
  }
  return false;
};
