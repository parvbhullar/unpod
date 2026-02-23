import {StyledCardIcon, StyledCheckableTag} from './index.styled';
import {Flex, Typography} from 'antd';
import {useIntl} from 'react-intl';

const {Text} = Typography;

type ToneItem = {
  key: string;
  label: string;
  icon?: string;
  color?: string;
};

type ToneCardProps = {
  item: ToneItem;
  handleChange: (key: string, checked: boolean) => void;
  isChecked: (key: string) => boolean;
};

const ToneCard = ({item, handleChange, isChecked}: ToneCardProps) => {
  const {formatMessage} = useIntl();

  return (
    <StyledCheckableTag
      key={item.key}
      checked={isChecked(item.key)}
      onChange={(checked: boolean) => handleChange(item.key, checked)}
    >
      <Flex justify="center" align="center" gap={10}>
        {item.icon && (
          <StyledCardIcon style={{color: item.color}}>
            {item.icon}
          </StyledCardIcon>
        )}
        <Text strong style={{margin: 0, whiteSpace: 'nowrap'}}>
          {formatMessage({id: item.label})}
        </Text>
      </Flex>
    </StyledCheckableTag>
  );
};

export default ToneCard;
