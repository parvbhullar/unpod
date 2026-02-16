import { Typography } from 'antd';
import { StyledLabel, StyledRoot } from './index.styled';
import { useIntl } from 'react-intl';
import type { ReactNode } from 'react';

const { Text } = Typography;

type LabelItem = {
  name: string;
  slug: string;
  icon?: ReactNode;
};

type LabelsProps = {
  data: LabelItem[];
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  multiSelect?: boolean;
};

const Labels = ({
  data,
  value,
  onChange,
  multiSelect = false,
}: LabelsProps) => {
  const { formatMessage } = useIntl();

  const handleChange = (checked: boolean, slug: string) => {
    if (!onChange) return;
    if (multiSelect) {
      // Multi-select: value is an array
      const currentValue = Array.isArray(value) ? value : [];
      if (checked) {
        // Add to array if not already present
        onChange([...currentValue, slug]);
      } else {
        // Remove from array
        onChange(currentValue.filter((item) => item !== slug));
      }
    } else {
      // Single select: value is a string
      onChange(checked ? slug : '');
    }
  };

  const isChecked = (slug: string) => {
    if (multiSelect) {
      return Array.isArray(value) && value.includes(slug);
    }
    return value === slug;
  };

  return (
    <StyledRoot>
      {data.map((label) => (
        <StyledLabel
          key={label.slug}
          checked={isChecked(label.slug)}
          onChange={(checked: boolean) => handleChange(checked, label.slug)}
        >
          {label.icon ? <Text>{label.icon}</Text> : null}
          <Text>{formatMessage({ id: label.name })}</Text>
        </StyledLabel>
      ))}
    </StyledRoot>
  );
};

export default Labels;
