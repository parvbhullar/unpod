import React from 'react';
import { Typography } from 'antd';
import { StyledCheckableTag } from './index.styled';

const { Title } = Typography;

type CheckboxCardProps = {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
};

const CheckboxCard: React.FC<CheckboxCardProps> = ({
  label,
  checked,
  onChange,
}) => {
  return (
    <StyledCheckableTag checked={checked} onChange={onChange}>
      <Title level={5} style={{ margin: 0 }}>
        {label}
      </Title>
    </StyledCheckableTag>
  );
};

export default CheckboxCard;
