import { Flex } from 'antd';
import { StyledPageHeader } from '../../Calls/Overview/Summary/index.styled';

const HeadingView = ({
  name,
  icon,
  extra,
}: {
  name: any;
  icon: any;
  extra?: any;
}) => {
  return (
    <Flex justify="space-between" align="center">
      <StyledPageHeader align="center" gap={12}>
        {icon}
        <h3>{name}</h3>
      </StyledPageHeader>
      {extra}
    </Flex>
  );
};

export default HeadingView;
