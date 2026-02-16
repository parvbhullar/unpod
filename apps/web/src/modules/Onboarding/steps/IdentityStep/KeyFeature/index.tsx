import { useCallback, useRef, useState } from 'react';
import { Typography } from 'antd';
import CheckboxCard from './FeatureCard';
import { TagWrapper, TonePersonalityContainer } from './index.styled';

const { Paragraph } = Typography;

type FeatureItem = { label: string } | string;

type KeyFeatureProps = {
  apiFeatures?: FeatureItem[];
  label?: string;
  onChange?: (values: string[]) => void;
  initialSelected?: string[];
};

const KeyFeature: React.FC<KeyFeatureProps> = ({
  apiFeatures = [],
  label,
  onChange,
  initialSelected = [],
}) => {
  const [selected, setSelected] = useState<string[]>(initialSelected);
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  const toggleFeature = useCallback((labelText: string) => {
    setSelected((prev) => {
      const next = prev.includes(labelText)
        ? prev.filter((f) => f !== labelText)
        : [...prev, labelText];
      onChangeRef.current?.(next);
      return next;
    });
  }, []);

  return (
    <TonePersonalityContainer>
      {label && <Paragraph strong>{label}</Paragraph>}
      <TagWrapper>
        {apiFeatures.map((feature) => {
          const labelText =
            typeof feature === 'string' ? feature : feature.label;
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
