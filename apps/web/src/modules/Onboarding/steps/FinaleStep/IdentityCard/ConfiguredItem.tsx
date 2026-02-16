import React from 'react';
import { Typography } from 'antd';
import { StyledDetailsRow, StyledTextWrapper } from './index.styled';

const { Text, Paragraph } = Typography;

type ConfiguredItemProps = {
  label: string;
  value: React.ReactNode;
};

const ConfiguredItem: React.FC<ConfiguredItemProps> = ({ label, value }) => {
  const isString = typeof value === 'string';
  return (
    <StyledDetailsRow>
      <Text style={{ width: '100%' }}>{label}</Text>
      {isString ? (
        <div
          style={{ whiteSpace: 'nowrap', fontWeight: 600 }}
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
              tooltip: value,
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
