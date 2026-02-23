import {StyledCardIcon, StyledCheckableTag, StyledSubtitle,} from './index.styled';
import {Flex, Typography} from 'antd';
import type {ReactNode} from 'react';
import {useIntl} from 'react-intl';

const {Text} = Typography;

type CheckboxItem = {
  key: string | number;
  label: string;
  desc?: string;
  icon?: ReactNode;
  color?: string;
};

type CheckboxCardProps = {
  item: CheckboxItem;
  handleChange: (label: string, checked: boolean) => void;
  isChecked: (label: string) => boolean;
};

const CheckboxCard = ({item, handleChange, isChecked}: CheckboxCardProps) => {
  const {formatMessage} = useIntl();

  return (
    <StyledCheckableTag
      key={item.key}
      checked={isChecked(item.label)}
      onChange={(checked) => handleChange(item.label, checked)}
    >
      {item.icon && (
        <StyledCardIcon style={{color: item.color}}>
          {item.icon}
        </StyledCardIcon>
      )}
      <Flex vertical justify="center" align="center">
        <Text strong style={{margin: 0}}>
          {formatMessage({id: item.label})}
        </Text>
        <StyledSubtitle type="secondary">
          {formatMessage({id: item.desc})}
        </StyledSubtitle>
      </Flex>
    </StyledCheckableTag>
  );
};

export default CheckboxCard;
