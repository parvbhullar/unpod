import type { ReactNode } from 'react';
import { Typography } from 'antd';
import { StyledLabel, StyledRoot } from './index.styled';

const { Text } = Typography;

type LabelItem = {
  slug?: string;
  name?: string;
  icon?: ReactNode;
};

type LabelsProps = {
  data: LabelItem[];
  value?: string;
  onChange: (value: string) => void;
};

const Labels = ({ data, value, onChange }: LabelsProps) => {
  return (
    <StyledRoot>
      {data.map((label) => {
        const slug = label.slug || '';
        return (
          <StyledLabel
            key={slug || label.name || ''}
            checked={value === slug}
            onChange={(checked) =>
              onChange(checked ? (slug === 'inbox' ? 'primary' : slug) : '')
            }
          >
            {label.icon ? <Text>{label.icon}</Text> : null}
            <Text>{label.name}</Text>
          </StyledLabel>
        );
      })}
    </StyledRoot>
  );
};

export default Labels;
