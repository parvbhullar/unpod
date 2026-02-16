import React from 'react';
import dynamic from 'next/dynamic';
import { Typography } from 'antd';
import { TagWrapper, TonePersonalityContainer } from './index.styled';

const { Paragraph } = Typography;

type PurposeItem = {
  key: string;
  label: string;
};

type PurposeListProps = {
  value?: string | null;
  onChange?: (value: string | null) => void;
  items: PurposeItem[];
  label: string;
  title?: boolean;
};

type CheckboxCardProps = {
  item: PurposeItem;
  handleChange: (labelText: string, checked: boolean) => void;
  isChecked: (labelToCheck: string) => boolean;
};

const CheckboxCard = dynamic<CheckboxCardProps>(
  () => import('@unpod/modules/AppIdentityAgentModule/CheckboxCard'),
  { ssr: false },
);

const PurposeList: React.FC<PurposeListProps> = ({
  value,
  onChange,
  items,
  label,
  title = true,
}) => {
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
