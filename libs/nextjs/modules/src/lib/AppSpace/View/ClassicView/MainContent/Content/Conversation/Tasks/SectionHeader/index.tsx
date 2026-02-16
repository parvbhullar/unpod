import { StyledFlex, StyledTaskCount } from './index.styled';
import { Typography } from 'antd';

const { Title } = Typography;

const SectionHeader = ({ lable, count }: { lable: string; count: number }) => {
  return (
    <StyledFlex justify="space-between" align="center">
      <Title className="mb-0" level={5}>
        {lable}
      </Title>
      <StyledTaskCount>{count}</StyledTaskCount>
    </StyledFlex>
  );
};

export default SectionHeader;
