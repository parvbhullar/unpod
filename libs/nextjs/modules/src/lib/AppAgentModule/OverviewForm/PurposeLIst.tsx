import {Typography} from 'antd';
import {TagWrapper, TonePersonalityContainer} from './index.styled';
import CheckboxCard from '../../AppIdentityAgentModule/CheckboxCard';

const {Paragraph} = Typography;

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
  const onLabelChange = (newLabel: string, checked: boolean) => {
    const foundItem = items.find((item) => item.label === newLabel);
    if (foundItem) {
      onChange?.(checked ? newLabel : null);
    }
  };

  const isChecked = (labelToCheck: string) => {
    return value === labelToCheck;
  };

  return (
    <TonePersonalityContainer>
      {title && <Paragraph strong>{label}</Paragraph>}
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
