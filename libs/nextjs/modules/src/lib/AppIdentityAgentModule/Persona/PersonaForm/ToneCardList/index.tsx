import { Typography } from 'antd';
import { TagWrapper, TonePersonalityContainer } from './index.styled';
import ToneCard from './ToneCard';

const { Paragraph } = Typography;

type ToneItem = {
  key: string;
  label: string;
  icon?: string;
  color?: string;
};

type ToneCardListProps = {
  value?: string;
  onChange?: (value: string) => void;
  items: ToneItem[];
  label: string;
};

const ToneCardList = ({ value, onChange, items, label }: ToneCardListProps) => {
  const onChangePersonality = (selectedKey: string) => {
    const newValue = value === selectedKey ? '' : selectedKey;
    onChange?.(newValue);
  };

  const isChecked = (key: string) => value === key;

  return (
    <TonePersonalityContainer>
      <Paragraph strong>{label}</Paragraph>
      <TagWrapper>
        {items.map((item: ToneItem) => (
          <ToneCard
            item={item}
            key={item.key}
            handleChange={onChangePersonality}
            isChecked={isChecked}
          />
        ))}
      </TagWrapper>
    </TonePersonalityContainer>
  );
};

export default ToneCardList;
