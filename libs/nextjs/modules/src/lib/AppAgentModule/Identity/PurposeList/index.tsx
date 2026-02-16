import { Typography } from 'antd';
import { TagWrapper, TonePersonalityContainer } from './index.styled';
import CheckboxCard from '../../../AppIdentityAgentModule/CheckboxCard';

const { Paragraph } = Typography;

type PurposeItem = {
  key: string;
  label: string;
  [key: string]: any;
};

type PurposeListProps = {
  value?: string | null;
  onChange?: (value: string | null) => void;
  items: PurposeItem[];
  label?: string;
  title?: boolean;
};

const PurposeList = ({
  value,
  onChange,
  items,
  label,
  title = true,
}: PurposeListProps) => {
  const isChecked = (labelToCheck: string) => {
    const found = items.find((item) => item.label === labelToCheck);
    return found?.key === value;
  };

  const onLabelChange = (labelText: string, checked: boolean) => {
    const foundItem = items.find((item) => item.label === labelText);

    if (foundItem) {
      onChange?.(checked ? foundItem.key : null);
    }
  };
  return (
    <TonePersonalityContainer>
      {label && <Paragraph strong>{label}</Paragraph>}
      <TagWrapper>
        {items.map((item) => (
          <CheckboxCard
            item={item}
            key={item.key}
            handleChange={onLabelChange}
            isChecked={isChecked}
          />
        ))}
      </TagWrapper>
    </TonePersonalityContainer>
  );
};

export default PurposeList;
