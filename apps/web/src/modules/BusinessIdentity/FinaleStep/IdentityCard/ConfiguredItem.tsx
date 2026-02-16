import React from 'react';
import { Typography } from 'antd';
import { StyledDetailsRow, StyledTextWrapper } from './index.styled';

const { Text, Paragraph } = Typography;

type ConfiguredItemProps = {
  label: string;
  value: string | React.ReactNode;
};

const ConfiguredItem = ({ label, value }: ConfiguredItemProps) => {
  const isString = typeof value === 'string';
  const tooltipValue = isString ? value : String(value);
  return (
    <StyledDetailsRow>
      <Text style={{ width: '100%' }}>{label}</Text>
      {isString ? (
        <div
          style={{ fontWeight: 600 }}
          dangerouslySetInnerHTML={{ __html: value }}
        />
      ) : (
        <StyledTextWrapper>
          <Paragraph
            strong
            style={{ margin: 0 }}
            ellipsis={{
              rows: 2,
              expandable: false,
              tooltip: tooltipValue,
            }}
          >
            {value}
          </Paragraph>
        </StyledTextWrapper>
      )}
    </StyledDetailsRow>
  );
};

export default ConfiguredItem;
