import type { ReactNode } from 'react';
import React from 'react';
import styled from 'styled-components';
import AppIcon from '@unpod/components/common/AppIcon';

export const StyledItemCell = styled.div`
  display: flex;
  gap: 0 16px;
  flex-direction: row;
  text-align: left;
  border-radius: ${({ theme }) => theme.radius.base}px;
  padding: 12px;
  max-width: 780px;
  cursor: pointer;
  border: 1px solid ${({ theme }) => theme.border.color};

  @media (max-width: ${({ theme }) => theme.breakpoints.sm}px) {
    flex-direction: column;
    text-align: center;
  }

  &.active,
  &:hover,
  &:focus,
  &:active {
    color: ${({ theme }) => theme.palette.primary};
    border: 1px solid ${({ theme }) => theme.palette.primary};
  }

  & img {
    width: 48px;
    height: 48px;
  }
`;
export const StyledItem = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;

  & div {
    font-size: 16px;
    font-weight: 600;
  }

  & p {
    font-size: 14px;
    font-weight: 400;
    margin-bottom: 0;
  }
`;
export type ItemCellData = {
  slug?: string;
  name?: string;
  description?: string;
  icon?: ReactNode | string;
  [key: string]: unknown;
};

type ItemCellProps = {
  item: ItemCellData;
  selectedItem: string[] | string;
  onSelectAccount: (item: ItemCellData) => void;
};

const ItemCell = ({ item, selectedItem, onSelectAccount }: ItemCellProps) => {
  return (
    <StyledItemCell
      className={
        Array.isArray(selectedItem)
          ? selectedItem.includes(item.slug ?? '')
            ? 'active'
            : ''
          : selectedItem === item?.slug
            ? 'active'
            : ''
      }
      onClick={() => onSelectAccount(item)}
    >
      {typeof item?.icon === 'string' ? (
        <AppIcon title={item?.name} icon={item?.icon} />
      ) : (
        item?.icon
      )}

      <StyledItem>
        <div>{item.name}</div>
        <p>{item.description}</p>
      </StyledItem>
    </StyledItemCell>
  );
};

export default ItemCell;
