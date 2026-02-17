export type ItemWithCost = {
  cost?: number;
  quantity?: number;
  tax_percentage?: number;
};

export const getItemAmount = (item: ItemWithCost): number => {
  return +((item.cost || 0) * (item.quantity || 0)).toFixed(8);
};

export const getItemTaxableAmount = (item: ItemWithCost): number => {
  return +(getItemAmount(item) - 0).toFixed(8);
};

export const getTaxAmount = (item: ItemWithCost): number => {
  return +(
    (getItemTaxableAmount(item) * (item.tax_percentage || 0)) /
    100
  ).toFixed(8);
};

export const getItemTotalAmount = (item: ItemWithCost): number => {
  const taxableAmount = getItemTaxableAmount(item);
  const taxAmount = getTaxAmount(item);

  const totalAmount = taxableAmount + taxAmount;

  return +totalAmount.toFixed(8);
};

export const getAllItemsAmount = (
  items: ItemWithCost[] | null | undefined,
): number => {
  let value = 0;
  items?.map((item) => {
    value += getItemAmount(item);
    return item;
  });

  return +value.toFixed(8);
};

export const getAllTaxAmount = (
  items: ItemWithCost[] | null | undefined,
): number => {
  let value = 0;
  items?.map((item) => {
    value += getTaxAmount(item);
    return item;
  });

  return +value.toFixed(8);
};

export const getTotalAmount = (
  items: ItemWithCost[] | null | undefined,
): number => {
  let value = 0;
  items?.map((item) => {
    value += getItemTotalAmount(item);
    return item;
  });

  return +value.toFixed(8);
};
