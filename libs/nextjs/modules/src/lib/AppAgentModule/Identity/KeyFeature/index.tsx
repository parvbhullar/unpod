import { useEffect, useState } from 'react';
import { TagWrapper, TonePersonalityContainer } from './index.styled';
import { Typography } from 'antd';
import CheckboxCard from './FeatureCard';

const { Paragraph } = Typography;

type KeyFeatureProps = {
  apiFeatures?: Array<string | { label?: string }>;
  label?: string;
  onChange?: (selected: string[]) => void;
  initialSelected?: string[];
};

const KeyFeature = ({
  apiFeatures = [],
  label,
  onChange,
  initialSelected = [],
}: KeyFeatureProps) => {
  const [selected, setSelected] = useState<string[]>(initialSelected);

  const toggleFeature = (labelText: string) => {
    setSelected((prev) =>
      prev.includes(labelText)
        ? prev.filter((f) => f !== labelText)
        : [...prev, labelText],
    );
  };

  useEffect(() => {
    if (selected) onChange?.(selected);
  }, [selected, onChange]);

  return (
    <TonePersonalityContainer>
      {label && <Paragraph strong>{label}</Paragraph>}
      <TagWrapper>
        {apiFeatures.map((feature) => {
          const labelText =
            typeof feature === 'string' ? feature : feature.label || '';
          return (
            <CheckboxCard
              key={labelText}
              label={labelText}
              checked={selected.includes(labelText)}
              onChange={() => toggleFeature(labelText)}
            />
          );
        })}
      </TagWrapper>
    </TonePersonalityContainer>
  );
};

export default KeyFeature;
