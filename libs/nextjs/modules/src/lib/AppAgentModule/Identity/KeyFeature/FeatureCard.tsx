import { Typography } from 'antd';
import { StyledCheckableTag } from './index.styled';

const { Title } = Typography;

type FeatureCardProps = {
  label: string;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
};

const CheckboxCard = ({ label, checked, onChange }: FeatureCardProps) => {
  return (
    <StyledCheckableTag checked={!!checked} onChange={onChange}>
      <Title level={5} style={{ margin: 0 }}>
        {label}
      </Title>
    </StyledCheckableTag>
  );
};

export default CheckboxCard;
