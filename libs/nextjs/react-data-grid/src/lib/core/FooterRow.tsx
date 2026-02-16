import React, { useMemo, useState } from 'react';
import styled from 'styled-components';
import type { MenuProps } from 'antd';
import { Dropdown } from 'antd';
import { VscBlank } from 'react-icons/vsc';
import { MdArrowDropDown, MdCheck } from 'react-icons/md';
import { rgba } from 'polished';
import { SelectCellState } from './DataGrid';
import { getMinMaxIdx } from './utils';

const StyledFooterRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: ${({ theme }: { theme: any }) => theme.backgroundColor};
  padding: 8px 8px 10px;
  position: sticky;
  bottom: 0;
`;

const StyledHandle = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background-color: ${({ theme }: { theme: any }) =>
    rgba(theme.primaryColor, 0.17)};
  border-radius: 8px;

  & .dropdown-arrow {
    font-size: 20px;
    transition: all 0.4s ease;
    rotate: 360deg;
  }

  &.ant-dropdown-open .dropdown-arrow {
    rotate: 180deg;
  }
`;

type MenuItem = {
  key: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  danger?: boolean;
};

const iconStyle = { fontSize: 16 };

type FooterRowProps = {
  rows: readonly any[];
  columns: readonly any[];
  selectedPosition: SelectCellState;
  draggedOverCellIdx: number;
  draggedOverRowIdx: number;
};

const FooterRow = ({
  selectedPosition,
  draggedOverCellIdx,
  draggedOverRowIdx,
  rows,
  columns,
  ...restProps
}: FooterRowProps) => {
  const { idx, rowIdx } = selectedPosition;
  const [startIdx, endIdx] = getMinMaxIdx(idx, draggedOverCellIdx);
  const totalSelectedCells = endIdx - startIdx + 1;
  const [startRowIdx, endRowIdx] = getMinMaxIdx(rowIdx, draggedOverRowIdx);
  const totalSelectedRows = endRowIdx - startRowIdx + 1;

  const [activeMenu, setActiveMenu] = useState<MenuItem | null>(null);
  const [activeKey, setActiveKey] = useState('sum');

  const items: MenuProps['items'] = useMemo(() => {
    const menus: MenuItem[] = [];

    if (
      startIdx >= 0 &&
      startRowIdx >= 0 &&
      (startIdx < endIdx || startRowIdx < endRowIdx)
    ) {
      const column = columns[startIdx]; // get the cell
      let numbersCount = 0;
      let totalSum = 0;
      const numbersArray: number[] = [];

      if (startIdx === endIdx && column.dataType === 'number') {
        for (let i = startRowIdx; i <= endRowIdx; i++) {
          const row = rows[i]; // get the row
          const numVal = +row[column.dataIndex];
          if (isNaN(numVal)) {
            totalSum += 0;
          } else {
            numbersCount++;
            totalSum += numVal;
            numbersArray.push(numVal);
          }
        }
      }

      const minValue = numbersCount > 0 ? Math.min(...numbersArray) : 0;
      const maxValue = numbersCount > 0 ? Math.max(...numbersArray) : 0;

      if (totalSum > 0) {
        menus.push({
          key: 'sum',
          label: `Sum: ${totalSum}`,
          icon: <VscBlank style={iconStyle} />,
        });
      }

      if (numbersCount > 0 && totalSum > 0) {
        menus.push({
          key: 'avg-val',
          label: `Avg: ${totalSum / numbersCount}`,
          icon: <VscBlank style={iconStyle} />,
        });
      }

      if (minValue > 0) {
        menus.push({
          key: 'min',
          label: `Min: ${minValue}`,
          icon: <VscBlank style={iconStyle} />,
        });
      }

      if (maxValue > 0) {
        menus.push({
          key: 'max',
          label: `Max: ${maxValue}`,
          icon: <VscBlank style={iconStyle} />,
        });
      }

      menus.push({
        key: 'count',
        label: `Count: ${totalSelectedCells * totalSelectedRows}`,
        icon: <VscBlank style={iconStyle} />,
      });

      if (numbersCount > 0) {
        menus.push({
          key: 'count-numbers',
          label: `Count Numbers: ${numbersCount}`,
          icon: <VscBlank style={iconStyle} />,
        });
      }

      let currentKey = activeKey;
      let currentItem = menus.find((item) => item?.key === activeKey);

      if (!currentItem) {
        currentItem = menus[0];
        currentKey = currentItem.key;
      }

      setActiveMenu(currentItem);

      return menus.map((item) => {
        if (item.key === currentKey) {
          return { ...item, icon: <MdCheck style={iconStyle} /> };
        }

        return item;
      });
    }

    return [];
  }, [
    activeKey,
    startIdx,
    endIdx,
    startRowIdx,
    endRowIdx,
    totalSelectedCells,
    totalSelectedRows,
  ]);

  const handleMenuItemClick: MenuProps['onClick'] = ({ key }) => {
    setActiveKey(key);
    setActiveMenu(
      (items.find((item) => item?.key === key) || null) as MenuItem,
    );
  };

  return items.length > 0 ? (
    <StyledFooterRow>
      <div />
      <Dropdown
        menu={{ items, onClick: handleMenuItemClick }}
        trigger={['click']}
      >
        <StyledHandle>
          {activeMenu?.label}
          <MdArrowDropDown className="dropdown-arrow" />
        </StyledHandle>
      </Dropdown>
    </StyledFooterRow>
  ) : null;
};

export default FooterRow;
