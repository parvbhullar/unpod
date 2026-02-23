import {Select} from 'antd';
import styled from 'styled-components';
import {RenderEditSelectCellProps} from '../models/data-grid';

const StyledSelect = styled(Select)`
  vertical-align: top;

  &.ant-select {
    height: 100%;
    width: 100%;

    &:not(.ant-select-customize-input) .ant-select-selector {
      border-radius: 2px;
      border-width: 2px;
    }
  }
`;

const {Option} = Select;

const SelectInput = <TRow, TSummaryRow>({
                                          row,
                                          column,
                                          onRowChange,
                                          onClose,
                                          options,
                                        }: RenderEditSelectCellProps<TRow, TSummaryRow>) => {
  return (
    <StyledSelect
      size="small"
      value={row[column.dataIndex as keyof TRow]}
      onChange={(newValue) =>
        onRowChange({...row, [column.dataIndex]: newValue})
      }
      onBlur={() => onClose(true, false)}
    >
      {options.map((option, index) => (
        <Option key={index} value={option}>
          {option}
        </Option>
      ))}
    </StyledSelect>
  );
};

export default SelectInput;
