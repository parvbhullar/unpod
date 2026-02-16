import { Typography } from 'antd';
import { TagWrapper, TonePersonalityContainer } from './index.styled';
import CheckboxCard from '../../CheckboxCard';

const { Paragraph } = Typography;

type PersonalityItem = {
  key: string;
  label: string;
  desc?: string;
};

type PersonalityListProps = {
  value?: string;
  onChange?: (value: string) => void;
  items: PersonalityItem[];
  label: string;
};

const PersonalityList = ({
  value,
  onChange,
  items,
  label,
}: PersonalityListProps) => {
  const onChangePersonality = (selectedLabel: string) => {
    const newValue = value === selectedLabel ? '' : selectedLabel;
    onChange?.(newValue);
  };

  const isChecked = (newLabel: string) => value === newLabel;

  return (
    <TonePersonalityContainer>
      <Paragraph strong>{label}</Paragraph>
      <TagWrapper>
        {items.map((item: PersonalityItem) => (
          <CheckboxCard
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

export default PersonalityList;
