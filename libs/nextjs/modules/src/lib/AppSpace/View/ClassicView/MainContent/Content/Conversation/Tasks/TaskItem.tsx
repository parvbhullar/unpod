import {
  StyledAvatar,
  StyledDescription,
  StyledFlex,
  StyledText,
} from './index.styled';
import { Flex, Typography } from 'antd';

const { Text } = Typography;

const TaskItem = ({ item, avatar }: { item: any; avatar?: any }) => {
  return (
    <StyledFlex align="center" gap={10}>
      {item.avatar ? (
        <StyledAvatar shape="square" size={36} src={item.avatar} />
      ) : (
        avatar
      )}
      <Flex vertical gap={2} flex={1}>
        {item.status && item.status === 'completed' ? (
          <StyledText strong>{item.title}</StyledText>
        ) : (
          <Text strong>{item.title}</Text>
        )}
        <StyledDescription type="secondary">{item.meta}</StyledDescription>
      </Flex>
    </StyledFlex>
  );
};

export default TaskItem;
