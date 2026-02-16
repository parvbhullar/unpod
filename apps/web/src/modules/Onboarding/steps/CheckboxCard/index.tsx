import React from 'react';
import {
  StyledCardIcon,
  StyledCheckableTag,
  StyledSubtitle,
} from './index.styled';
import { Typography } from 'antd';

const { Title } = Typography;

type CheckboxItem = {
  key: string;
  label: string;
  desc?: string;
  icon?: React.ReactNode;
  color?: string;
};

type CheckboxCardProps = {
  item: CheckboxItem;
  handleChange: (label: string, checked: boolean) => void;
  isChecked: (label: string) => boolean;
};

const CheckboxCard: React.FC<CheckboxCardProps> = ({
  item,
  handleChange,
  isChecked,
}) => {
  return (
    <StyledCheckableTag
      key={item.key}
      checked={isChecked(item.label)}
      onChange={(checked) => handleChange(item.label, checked)}
    >
      {item.icon && (
        <StyledCardIcon style={{ color: item.color }}>
          {item.icon}
        </StyledCardIcon>
      )}
      <Title level={5} style={{ margin: 0 }}>
        {item.label}
      </Title>
      <StyledSubtitle type="secondary">{item.desc}</StyledSubtitle>
    </StyledCheckableTag>
  );
};

export default CheckboxCard;
